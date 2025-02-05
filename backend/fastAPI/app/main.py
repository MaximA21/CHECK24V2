from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter



from prometheus_fastapi_instrumentator import Instrumentator

from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
from .utils.constants import POPULAR_TEAMS, POPULAR_NATIONS, POPULAR_TOURNAMENTS
from .core.database import Database
from .services.game_service import GameService
from .services.package_service import PackageService
from .services.api_football_service import APIFootballService
from .core.monitoring import ProfilingMiddleware
from .core.performance_tracker import tracker
from .utils.formatting import format_date_iso, format_package_for_response, format_game_for_response


# Limiter initialisieren
limiter = Limiter(key_func=get_remote_address)

resource = Resource(attributes={
    "service.name": "streaming-api"
})

tracer_provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter())
tracer_provider.add_span_processor(processor)
trace.set_tracer_provider(tracer_provider)

meter_provider = MeterProvider(resource=resource)
metric_exporter = OTLPMetricExporter(endpoint="http://localhost:4317")

app = FastAPI()

FastAPIInstrumentor.instrument_app(app)

# Instrumentator konfigurieren
instrumentator = Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics"]
)
Instrumentator().instrument(app).expose(app)

# Limiter zur App hinzufügen
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(ProfilingMiddleware)


@app.get("/api/v1/suggestions/")
@limiter.limit("30/minute")
async def get_suggestions(request: Request):
    try:
        return {
            "status": "success",
            "popular_teams": POPULAR_TEAMS,
            "nations": POPULAR_NATIONS,
            "tournaments": POPULAR_TOURNAMENTS
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/v1/test/")
async def test():
    return {"status": "ok", "message": "API is running"}


@app.get("/debug/performance")
async def get_performance_stats():
    """Endpoint für Performance-Statistiken."""
    return tracker.get_stats()

tracer = trace.get_tracer(__name__)

@app.get("/api/v1/streaming-combinations/")
@limiter.limit("20/minute")
async def find_streaming_combinations(
    request: Request,
    teams: List[str] = Query(..., description="Teams to watch"),
    max_combinations: Optional[int] = Query(3, description="Maximum number of packages"),
    live_only: Optional[bool] = Query(True, description="Only include live streams"),
    start_date: Optional[datetime] = Query(datetime.now(), description="Optional start date"),

):
    with tracer.start_as_current_span("find_combinations") as span:
        try:
            db = Database()
            api_service = APIFootballService()
            game_service = GameService(db, api_service)
            package_service = PackageService(db)

            request_time = datetime.now()

            # 1. Hole analysierte Spiele
            with tracer.start_as_current_span("get_analyzed_games") as game_span:
                analysis = await game_service.get_analyzed_games(
                    teams=teams,
                    start_date=start_date
                )
                game_span.set_attribute("teams_count", len(teams))

            # Finde beste Paket-Kombination
            with tracer.start_as_current_span("find_best_combination") as pkg_span:
                result = await package_service.find_best_combination(
                    games=analysis["games"],
                    max_packages=max_combinations,
                    require_live=live_only
                )
                pkg_span.set_attribute("packages_found", len(result["selected_packages"]))

            return {
                "meta": {
                    "serverTime": format_date_iso(request_time),
                    "requestDurationMS": int((datetime.now() - request_time).total_seconds() * 1000),
                    "teamsRequested": teams,
                    "timeRange": {
                        "start": format_date_iso(analysis["timeframe"]["start"]),
                        "end": format_date_iso(analysis["timeframe"]["end"]),
                    },
                    "mainLeague": analysis["main_league"]
                },
                "data": {
                    "selected_packages": [
                        format_package_for_response(pkg)
                        for pkg in result["selected_packages"]
                    ],
                    "total_cost": result["total_cost"] / 100,  # Convert cents to euros
                    "coverage_ratio": f"{result['coverage_ratio'] * 100:.1f}%",
                    "weighted_coverage": f"{result['weighted_coverage'] * 100:.1f}%",
                    "uncovered_games": [
                        format_game_for_response(g)
                        for g in result["uncovered_games"]
                    ],
                    "unstreamable_games": [
                        format_game_for_response(g)
                        for g in analysis["unstreamable_games"]
                    ]
                },
                "status": "success"
            }

        except Exception as e:
            error_response = {
                "meta": {
                    "serverTime": format_date_iso(datetime.now()),
                },
                "error": str(e),
                "status": "error"
            }
            raise HTTPException(
                status_code=500,
                detail=error_response
            )


@app.get("/api/v1/cache-test/")
async def test_cache():
    api_service = APIFootballService()

    # Test 1: Erste Abfrage (sollte API call machen)
    start_time = datetime.now()
    result1 = await api_service.get_table_positions(
        tournament="Bundesliga",
        team="Bayern München",
        game_date=datetime.now()
    )
    time1 = (datetime.now() - start_time).total_seconds()

    # Test 2: Zweite Abfrage (sollte aus Cache kommen)
    start_time = datetime.now()
    result2 = await api_service.get_table_positions(
        tournament="Bundesliga",
        team="Borussia Dortmund",
        game_date=datetime.now()
    )
    time2 = (datetime.now() - start_time).total_seconds()

    return {
        "first_call": {
            "duration": round(time1, 3),
            "result": result1
        },
        "second_call": {
            "duration": round(time2, 3),
            "result": result2
        },
        "cache_working": time2 < time1
    }


@app.get("/api/v1/redis-test/")
async def test_redis():
    api_service = APIFootballService()

    test_key = "test:connection"
    test_value = "hello"

    try:
        api_service.redis.set(test_key, test_value)

        read_value = api_service.redis.get(test_key)

        api_service.redis.delete(test_key)

        return {
            "redis_working": True,
            "test_value": read_value,
            "connection_info": {
                "host": api_service.redis.connection_pool.connection_kwargs["host"],
                "port": api_service.redis.connection_pool.connection_kwargs["port"]
            }
        }
    except Exception as e:
        return {
            "redis_working": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.get("/api/v1/clear-cache/")
async def clear_cache():
    api_service = APIFootballService()
    try:
        # Löscht ALLE Keys
        api_service.redis.flushall()
        return {"message": "Cache erfolgreich geleert"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/search/")
async def search_teams(query: str):
    db = Database()

    if len(query) < 2:
        return {"suggestions": []}

    try:
        search_query = """
        SELECT DISTINCT team_home as team 
        FROM game 
        WHERE team_home ILIKE :query || '%'
        UNION 
        SELECT DISTINCT team_away as team
        FROM game 
        WHERE team_away ILIKE :query || '%'
        LIMIT 10
        """

        result = await db.execute(search_query, {
            "query": query
        })

        suggestions = [row["team"] for row in result]
        return {"suggestions": suggestions}

    except Exception as e:
        return {"suggestions": [], "error": str(e)}