from typing import List, Dict
import math
from ....models.domain import Game


class SolutionEvaluator:
    def __init__(self, cost_calculator):
        self.cost_calculator = cost_calculator

    def evaluate(
            self,
            solution: List[Dict],
            games: List[Game],
    ) -> float:
        """
        Bewertet eine Lösung und gibt einen Score zurück.
        Höherer Score = bessere Lösung.
        """
        if not solution:
            return float('-inf')

        # Berechne Grundmetriken
        total_cost = 0
        covered_game_weights = {}  # Speichert für jedes Spiel das beste Gewicht

        # Evaluiere die Gesamtabdeckung
        for package in solution:
            # Kosten berechnen
            cost_info = self.cost_calculator.calculate_package_cost(
                package['package'],
                package['covered_games'],
            )
            total_cost += cost_info['total_cost']

            # Für jedes Spiel im Paket: Aktualisiere bestes Gewicht
            for game in package['covered_games']:
                if game.id not in covered_game_weights:
                    covered_game_weights[game.id] = game.total_weight

        # Berechne Score
        total_weight_covered = sum(covered_game_weights.values())
        total_weight = sum(game.total_weight for game in games)

        coverage_ratio = total_weight_covered / total_weight
        cost_factor = math.log(total_cost + 1)
        package_count_penalty = len(solution) / 4

        return (coverage_ratio * 1000) - cost_factor - package_count_penalty
