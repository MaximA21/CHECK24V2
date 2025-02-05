from typing import Dict, List
from ..models.domain import Game


class PackageCostCalculator:
    @staticmethod
    def get_available_subscription_types(package: Dict) -> List[str]:
        """Ermittelt verfügbare Abo-Typen"""
        available_types = []

        if package.get('monthly_price_cents') is not None:
            available_types.append("monthly")

        if package.get('monthly_price_yearly_subscription_in_cents') is not None:
            available_types.append("yearly")

        return available_types

    def calculate_package_cost(self, package: Dict, package_games: List[Game]) -> Dict:
        """Berechnet optimale Kosten für ein Paket"""
        available_types = self.get_available_subscription_types(package)

        # Wenn nur Jahresabo verfügbar
        if available_types == ["yearly"]:
            yearly_cost = package['monthly_price_yearly_subscription_in_cents'] * 12
            return {
                "total_cost": yearly_cost,
                "subscription_type": "yearly",
                "active_months": None
            }

        sorted_games = sorted(package_games, key=lambda g: g.starts_at)

        if not sorted_games:
            return {
                "total_cost": 0,
                "subscription_type": None,
                "active_months": None
            }

        # Berechne aktive Monate
        active_months = set()
        for game in sorted_games:
            game_month = game.starts_at.strftime('%Y-%m')
            active_months.add(game_month)

        # Berechne Kosten für beide Varianten
        monthly_price = package.get('monthly_price_cents')
        yearly_price = package.get('monthly_price_yearly_subscription_in_cents')

        # Wenn nur Monatsabo verfügbar
        if "yearly" not in available_types:
            monthly_total = len(active_months) * monthly_price
            return {
                "total_cost": monthly_total,
                "subscription_type": "monthly",
                "active_months": active_months
            }

        # Vergleiche Monats- und Jahresabo
        monthly_total = len(active_months) * monthly_price
        yearly_total = yearly_price * 12

        if monthly_total < yearly_total:
            return {
                "total_cost": monthly_total,
                "subscription_type": "monthly",
                "active_months": active_months
            }
        else:
            return {
                "total_cost": yearly_total,
                "subscription_type": "yearly",
                "active_months": None
            }
