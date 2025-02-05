from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
from ..core.database import Database
from ..models.domain import Game
from .api_football_service import APIFootballService
from . import league_service
from .weights.weight_calculator import WeightCalculator
from .pause_detector import PauseDetector
from ..utils.profiling import ProfilingBlock, profile_block


class GameService:
    def __init__(
            self,
            db: Database,
            api_service: APIFootballService
    ):
        self.db = db
        self.api_service = api_service
        self.weight_calculator = WeightCalculator(api_service)
        self.pause_detector = PauseDetector()

    async def _get_relevant_games(
            self,
            teams: List[str],
            start_date: datetime,
            end_date: datetime,
            tournament: Optional[str] = None
    ) -> Tuple[List[Game], List[Game]]:
        """DB-Call für Spiele, optional nur für ein Turnier."""

        query = """
        SELECT g.*, (so.game_id IS NOT NULL) as streamed
        FROM game g
        LEFT JOIN (
            SELECT DISTINCT game_id 
            FROM streaming_offer
        ) so ON g.id = so.game_id
        WHERE (g.team_home = ANY(:teams) OR g.team_away = ANY(:teams))
        AND g.starts_at BETWEEN :start_date AND :end_date
        """

        if tournament:
            query += ' AND g.tournament_name = :tournament'

        query +=" ORDER BY g.starts_at"

        streamable_games = []
        unstreamable_games = []

        result = await self.db.execute(query, {
            "teams": teams,
            "start_date": start_date,
            "end_date": end_date,
            "tournament": tournament
        })

        # Konvertierung anpassen
        for row in result:
            game = Game(
                id=row["id"],
                team_home=row["team_home"],
                team_away=row["team_away"],
                tournament=row["tournament_name"],
                starts_at=row["starts_at"],
                base_weight=1.0,
                phase_multiplier=1.0,
                importance_multiplier=1.0
            )
            if row["streamed"]:
                streamable_games.append(game)
            else:
                unstreamable_games.append(game)

        return streamable_games, unstreamable_games

    @profile_block("game_service.total")
    async def get_analyzed_games(
            self,
            teams: List[str],
            start_date: Optional[datetime] = datetime.now(timezone.utc)
    ) -> Dict:
        """Hauptanalyse in einem Durchgang mit minimaler Gewichtsberechnung"""

        if start_date.tzinfo is None:
            # Falls start_date ohne timezone übergeben wurde
            start_date = start_date.replace(tzinfo=timezone.utc)

        # 1. Hole Turniere und Hauptliga
        with ProfilingBlock("game_service.get_leagues"):
            tournaments = await league_service.get_team_tournaments(self.db, teams)
        with ProfilingBlock("game_service.get_main_league"):
            main_league = await league_service.get_main_league(self.db, teams)

        # 2. Hole erstmal nur Spiele der Hauptliga für 6 Monate
        temp_end = start_date + timedelta(days=180)
        with ProfilingBlock("game_service.get_main_league_games"):
            main_league_games = await self._get_relevant_games(
                teams=teams,
                start_date=start_date,
                end_date=temp_end,
                tournament=main_league
            )

        # 3. Finde Pausen nur anhand der Hauptliga-Spiele
        with ProfilingBlock("game_service.find_pauses"):
            main_league_pauses = self.pause_detector.find_pauses(main_league_games[0])  # [0] für streamable

        # 4. Bestimme Enddatum basierend auf Pausen
        min_end_date = start_date + timedelta(days=90)
        end_date = min_end_date  # Fallback

        for pause in sorted(main_league_pauses, key=lambda x: x["start"]):
            if pause["start"] >= min_end_date:
                end_date = pause["start"]
                break

        # 5. Jetzt erst hole alle relevanten Spiele für den finalen Zeitraum
        with ProfilingBlock("game_service.get_final_games"):
            streamable_games, unstreamable_games = await self._get_relevant_games(
                teams=teams,
                start_date=start_date,
                end_date=end_date
            )

        # 6. Gewichte nur die streamable Spiele
        with ProfilingBlock("game_service.calculate_weights"):
            weighted_games = await self.weight_calculator.calculate_weight(streamable_games)

        return {
            "timeframe": {
                "start": start_date,
                "end": end_date
            },
            "main_league": main_league,
            "games": weighted_games,
            "unstreamable_games": unstreamable_games,
            "pauses": main_league_pauses,
            "tournaments": tournaments
        }