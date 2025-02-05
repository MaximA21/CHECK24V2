import re
from typing import List

from ...models.domain import Game
from ...utils.weights import (
    TOURNAMENT_WEIGHTS,
    PHASE_MULTIPLIERS,
    IMPORTANCE_MULTIPLIERS
)
from ..api_football_service import APIFootballService
from ...utils.constants import LEAGUE_IDS


class WeightCalculator:
    def __init__(self, api_service: APIFootballService):
        self.api_service = api_service

    async def calculate_weight(self, games: List[Game]) -> List[Game]:
        """
              Berechnet das Gesamtgewicht für ein Spiel.
              Alle Teilgewichte werden asynchron berechnet.
              """
        game_list = []
        for game in games:
            base_weight = await self._calculate_tournament_weight(game)
            phase_multiplier = 1.0  # await self._calculate_phase_multiplier(game)
            importance_multiplier = 1.0  # await self._calculate_importance_multiplier(game)

            game.base_weight = base_weight
            game.phase_multiplier = 1.0  # phase_multiplier
            game.importance_multiplier = 1.0  # importance_multiplier
            game_list.append(game)

        return game_list


    @staticmethod
    async def _calculate_tournament_weight(game: Game) -> float:
        """Berechnet das Grundgewicht basierend auf dem Turnier."""
        # Entferne Saison-Pattern (z.B. 24/25 oder 2023/2024)
        base_name = re.sub(r'\s+\d{2,4}/\d{2,4}$', '', game.tournament)
        return TOURNAMENT_WEIGHTS.get(base_name, 0.4)

    async def _calculate_phase_multiplier(self, game: Game) -> float:
        """Berechnet den Phasen-Multiplikator basierend auf den API-Daten."""
        phase = await self.api_service.get_game_phase(
            tournament=game.tournament,
            game_date=game.starts_at
        )

        return PHASE_MULTIPLIERS.get(phase, PHASE_MULTIPLIERS["GROUP"])

    async def _calculate_importance_multiplier(self, game: Game) -> float:
        """
        Berechnet den Wichtigkeits-Multiplikator nur basierend auf Tabellenposition.
        """
        # Hole Tabellenpositionen
        home_pos, total_teams = await self.api_service.get_table_positions(
            tournament=game.tournament,
            team=game.team_home,
            game_date=game.starts_at
        )
        away_pos, _ = await self.api_service.get_table_positions(
            tournament=game.tournament,
            team=game.team_away,
            game_date=game.starts_at
        )

        # Titelkampf: Beide Teams in Top 3
        if home_pos <= 3 and away_pos <= 3:
            return IMPORTANCE_MULTIPLIERS["TITLE"]

        # Abstiegskampf: Beide Teams in letzten 3
        if home_pos >= total_teams - 3 and away_pos >= total_teams - 3:
            return IMPORTANCE_MULTIPLIERS["RELEGATION"]

        return IMPORTANCE_MULTIPLIERS["NORMAL"]
