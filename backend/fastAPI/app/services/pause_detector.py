from datetime import datetime, timezone
from typing import List, Dict
from ..models.domain import Game


class PauseDetector:
    def __init__(self):
        self.pause_factor = 2.0  # Faktor über Durchschnitt = Pause

    def find_pauses(self, games: List[Game]) -> List[Dict[str, datetime]]:
        """
        Hauptmethode zum Finden von Pausen.
        Wrapper für _find_tournament_pauses
        """
        return self._find_tournament_pauses(games)

    @staticmethod
    def _calculate_average_gap(games: List[Game]) -> float:
        """Berechnet durchschnittlichen Abstand zwischen Spielen."""
        if not games or len(games) < 2:
            return 0

        gaps = []

        for i in range(len(games) - 1):
            gap = games[i + 1].starts_at - games[i].starts_at
            gaps.append(gap.days)

        return sum(gaps) / len(gaps)

    def _find_tournament_pauses(
            self,
            games: List[Game]
    ) -> List[Dict[str, datetime]]:
        """Findet Pausen basierend auf durchschnittlichem Spielabstand."""
        if not games:
            return []

        sorted_games = sorted(games, key=lambda x: x.starts_at)
        avg_gap = self._calculate_average_gap(sorted_games)
        min_pause_days = avg_gap * self.pause_factor
        pauses = []

        # Prüfe Pausen zwischen Spielen
        for i in range(len(sorted_games) - 1):
            gap = sorted_games[i + 1].starts_at - sorted_games[i].starts_at
            if gap.days >= min_pause_days:
                pauses.append({
                    "tournament": sorted_games[i].tournament,
                    "start": sorted_games[i].starts_at.replace(tzinfo=timezone.utc),
                    "end": sorted_games[i + 1].starts_at.replace(tzinfo=timezone.utc),
                    "is_unusual": True  # Diese Pause ist länger als üblich
                })
        print(pauses)
        return pauses
