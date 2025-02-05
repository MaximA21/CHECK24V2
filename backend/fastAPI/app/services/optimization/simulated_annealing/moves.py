from typing import List, Dict
import random


class MoveOperator:
    def get_neighbor(
            self,
            current_solution: List[Dict],
            available_packages: List[Dict],
            coverage_map: Dict,
            max_packages: int
    ) -> List[Dict]:
        """
        Generiert eine neue Nachbarlösung durch zufällige Move-Operation.
        """
        move_ops = [
            self.swap_package,
            self.add_package,
            self.remove_package
        ]

        if len(current_solution) >= max_packages:
            move_ops.remove(self.add_package)
        if len(current_solution) <= 1:
            move_ops.remove(self.remove_package)

        move_op = random.choice(move_ops)
        return move_op(current_solution, available_packages, coverage_map, max_packages)

    def swap_package(
            self,
            solution: List[Dict],
            available_packages: List[Dict],
            coverage_map: Dict,
            max_packages: int
    ) -> List[Dict]:
        """Tauscht ein zufälliges Paket gegen ein anderes."""
        new_solution = solution.copy()

        # Wähle zufällig ein Paket zum Entfernen
        package_to_remove = random.choice(new_solution)
        new_solution.remove(package_to_remove)

        # Wähle zufällig ein neues Paket
        unused_packages = [p for p in available_packages
                           if not any(sp['package']['id'] == p['id']
                                      for sp in new_solution)]
        if unused_packages:
            new_package = random.choice(unused_packages)
            new_solution.append({
                'package': new_package,
                'covered_games': coverage_map[new_package['id']]['games']
            })

        return new_solution

    def add_package(
            self,
            solution: List[Dict],
            available_packages: List[Dict],
            coverage_map: Dict,
            max_packages: int
    ) -> List[Dict]:
        """Fügt ein neues Paket hinzu wenn möglich."""
        if len(solution) >= max_packages:
            return solution.copy()

        new_solution = solution.copy()
        unused_packages = [p for p in available_packages
                           if not any(sp['package']['id'] == p['id']
                                      for sp in new_solution)]

        if unused_packages:
            new_package = random.choice(unused_packages)
            new_solution.append({
                'package': new_package,
                'covered_games': coverage_map[new_package['id']]['games']
            })

        return new_solution

    def remove_package(
            self,
            solution: List[Dict],
            available_packages: List[Dict],
            coverage_map: Dict,
            max_packages: int
    ) -> List[Dict]:
        """Entfernt ein zufälliges Paket."""
        if len(solution) <= 1:
            return solution.copy()

        new_solution = solution.copy()
        package_to_remove = random.choice(new_solution)
        new_solution.remove(package_to_remove)
        return new_solution