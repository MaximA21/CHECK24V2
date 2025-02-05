from typing import Dict
from .base import PackageOptimizer
from ..package_cost_calculator import PackageCostCalculator


class GreedyOptimizer(PackageOptimizer):
    """Greedy"""

    def __init__(self, cost_calculator: PackageCostCalculator):
        self.cost_calculator = cost_calculator

    def optimize(self, games, packages, coverage_map, max_packages) -> Dict:
        selected_packages = []
        covered_game_ids = set()
        total_weight_covered = 0
        total_cost = 0

        # Solange wir max_packages nicht erreicht haben und noch Packages da sind
        for _ in range(max_packages):
            best_score = -1
            best_package_info = None

            # Berechne Scores basierend auf noch ungedeckten Spielen
            for package in packages:
                pkg_games = coverage_map[package['id']]['games']

                # Nur noch nicht abgedeckte Spiele zählen
                new_games = [g for g in pkg_games if g.id not in covered_game_ids]
                if not new_games:
                    continue

                weight_sum = sum(g.total_weight for g in new_games)
                cost_info = self.cost_calculator.calculate_package_cost(package, new_games)

                if cost_info["total_cost"] > 0:
                    score = weight_sum / cost_info["total_cost"]
                    if score > best_score:
                        best_score = score
                        best_package_info = {
                            'package': package,
                            'new_games': new_games,
                            'weight_sum': weight_sum,
                            'cost_info': cost_info
                        }

            if not best_package_info:
                break

            # Füge bestes Paket hinzu und aktualisiere covered_game_ids
            selected_packages.append({
                'package': best_package_info['package'],
                'covered_games': best_package_info['new_games'],
                'weight_sum': best_package_info['weight_sum'],
                'cost': best_package_info['cost_info']["total_cost"],
                'subscription_type': best_package_info['cost_info']["subscription_type"],
                'active_months': best_package_info['cost_info']["active_months"]
            })

            covered_game_ids.update(g.id for g in best_package_info['new_games'])
            total_weight_covered += best_package_info['weight_sum']
            total_cost += best_package_info['cost_info']["total_cost"]

        return {
            'selected_packages': selected_packages,
            'total_cost': total_cost,
            'coverage_ratio': len(covered_game_ids) / len(games),
            'weighted_coverage': total_weight_covered / sum(g.total_weight for g in games),
            'uncovered_games': [g for g in games if g.id not in covered_game_ids]
        }
