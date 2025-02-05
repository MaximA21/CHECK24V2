from typing import List, Dict
from ..base import PackageOptimizer
from .evaluator import SolutionEvaluator
from .moves import MoveOperator
from ....models.domain import Game
from ...optimization.greedy import GreedyOptimizer
import math
import random
import time
from ....utils.profiling import profile_block, ProfilingBlock


class SimulatedAnnealingOptimizer(PackageOptimizer):
    def __init__(
            self,
            cost_calculator,
            initial_temp: float = 100.0,
            cooling_rate: float = 0.98,
            min_temp: float = 0.01,
            max_iterations: int = 100000,
            time_limit: float = 10.0  # Zeitlimit in Sekunden
    ):
        self.cost_calculator = cost_calculator
        self.evaluator = SolutionEvaluator(cost_calculator)
        self.move_operator = MoveOperator()
        self.greedy_optimizer = GreedyOptimizer(cost_calculator)

        # SA Parameter
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.min_temp = min_temp
        self.max_iterations = max_iterations
        self.time_limit = time_limit

    @profile_block("sa_optimizer.total")
    async def optimize(
            self,
            games: List[Game],
            packages: List[Dict],
            coverage_map: Dict,
            max_packages: int
    ) -> Dict:

        # Starte mit Greedy-Lösung
        with ProfilingBlock("sa_optimizer.initial_solution"):
            greedy_solution = self.greedy_optimizer.optimize(
                games, packages, coverage_map, max_packages
            )

        current_solution = greedy_solution["selected_packages"]
        current_score = self.evaluator.evaluate(current_solution, games)

        # Beste Lösung tracken
        best_solution = current_solution
        best_score = current_score

        # Temperatur und Zeit initialisieren
        temperature = self.initial_temp
        start_time = time.time()

        # Hauptloop
        iteration = 0
        with ProfilingBlock("sa_optimizer.main_loop"):
            while (temperature > self.min_temp and
                   iteration < self.max_iterations and
                   time.time() - start_time < self.time_limit):

                # Generiere neue Lösung
                new_solution = self.move_operator.get_neighbor(
                    current_solution,
                    packages,
                    coverage_map,
                    max_packages
                )
                new_score = self.evaluator.evaluate(new_solution, games)

                # Berechne Akzeptanzwahrscheinlichkeit
                if self._should_accept(current_score, new_score, temperature):
                    current_solution = new_solution
                    current_score = new_score

                    # Update beste Lösung wenn nötig
                    if current_score > best_score:
                        best_solution = current_solution
                        best_score = current_score

                # Kühle ab
                temperature *= self.cooling_rate
                iteration += 1

        return self._format_result(best_solution, games, coverage_map)

    @staticmethod
    def _should_accept(current_score: float, new_score: float, temperature: float) -> bool:
        """
        Entscheidet, ob eine neue Lösung akzeptiert wird.
        Bessere Lösungen werden immer akzeptiert.
        Schlechtere mit einer temperaturabhängigen Wahrscheinlichkeit.
        """
        if new_score > current_score:
            return True

        delta = new_score - current_score
        probability = math.exp(delta / temperature)
        return random.random() < probability

    def _format_result(
            self,
            best_solution: List[Dict],
            games: List[Game],
            coverage_map: Dict,
    ) -> Dict:
        if not best_solution:
            return {
                'selected_packages': [],
                'total_cost': 0,
                'coverage_ratio': 0,
                'weighted_coverage': 0,
                'uncovered_games': games
            }

        # Berechne Coverage
        covered_game_ids = set()
        total_cost = 0
        total_weight_covered = 0
        total_weight = sum(game.total_weight for game in games)

        # Formatiere selected_packages
        selected_packages = []
        for package in best_solution:
            package_games = coverage_map[package['package']['id']]['games']
            new_games = [g for g in package_games if g.id not in covered_game_ids]

            cost_info = self.cost_calculator.calculate_package_cost(
                package['package'],
                package_games,
            )

            selected_packages.append({
                'package': package['package'],
                'covered_games': package_games,
                'cost': cost_info['total_cost'],
                'subscription_type': cost_info['subscription_type'],
                'active_months': cost_info.get('active_months')
            })

            covered_game_ids.update(g.id for g in new_games)
            total_weight_covered += sum(g.total_weight for g in new_games)
            total_cost += cost_info['total_cost']

        return {
            'selected_packages': selected_packages,
            'total_cost': total_cost,
            'coverage_ratio': len(covered_game_ids) / len(games),
            'weighted_coverage': total_weight_covered / total_weight,
            'uncovered_games': [g for g in games if g.id not in covered_game_ids]
        }
