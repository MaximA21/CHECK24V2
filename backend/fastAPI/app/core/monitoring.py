import time
from .performance_tracker import tracker
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..utils.profiling import start_profiling, get_profiling_data


class ProfilingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Starte Profiling für diesen Request
        start_time = time.time()
        start_profiling()

        # Führe Request aus
        response = await call_next(request)

        # Sammle Profiling-Daten
        duration = time.time() - start_time
        profiling_data = get_profiling_data()

        if profiling_data:
            # Tracker updaten
            tracker.add_request(
                path=request.url.path,
                duration=duration,
                measurements=profiling_data.measurements
            )
            # Header für Debugging
            response.headers['X-Total-Time'] = f"{duration:.3f}s"

        return response