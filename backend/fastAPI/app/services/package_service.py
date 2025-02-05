from typing import List, Dict
from ..core.database import Database
from .optimization.greedy import GreedyOptimizer
from .package_cost_calculator import PackageCostCalculator
from ..models.domain import Game
from ..services.optimization.simulated_annealing.optimizer import SimulatedAnnealingOptimizer
from ..utils.profiling import profile_block, ProfilingBlock


class PackageService:
    def __init__(self, db: Database):
        self.db = db
        self.cost_calculator = PackageCostCalculator()
        self.optimizer = GreedyOptimizer(self.cost_calculator)  # Später austauschbar
        self.sa_optimizer = SimulatedAnnealingOptimizer(self.cost_calculator)

    @profile_block("package_service.total")
    async def find_best_combination(
            self,
            games: List[Game],
            max_packages: int = 3,
            require_live: bool = True
    ) -> Dict:
        """
        Findet die beste Paket-Kombination basierend auf:
        - Gewichteten Spielen
        - Erkannten Pausen
        - Maximaler Paketanzahl
        - Live-Anforderung
        """

        # Hole verfügbare Pakete
        with ProfilingBlock("package_service.get_packages"):
            packages = await self._get_available_packages()

        # Finde Spiel-Abdeckung pro Paket
        with ProfilingBlock("package_service.build_coverage"):
            coverage_map = await self._get_coverage_map(games, packages, require_live)

        with ProfilingBlock("package_service.optimize"):
            # Bestimme unique Teams
            unique_teams = set()
            for game in games:
                unique_teams.add(game.team_home)
                unique_teams.add(game.team_away)

            result = await self.sa_optimizer.optimize(
                games=games,
                packages=packages,
                coverage_map=coverage_map,
                max_packages=max_packages
            )
        return result

    async def _get_available_packages(self) -> List[Dict]:
        """Holt alle verfügbaren Streaming-Pakete."""

        query = """
        SELECT 
            id,
            name,
            monthly_price_cents,
            monthly_price_yearly_subscription_in_cents
        FROM streaming_package
        """

        return await self.db.execute(query)

    async def _get_coverage_map(
            self,
            games: List[Game],
            packages: List[Dict],
            require_live: bool
    ) -> Dict:
        """
        Erstellt eine Map welches Paket welche Spiele abdeckt.
        Berücksichtigt Live/Highlight Anforderungen.
        """
        coverage_map = {}

        # Hole alle Streaming-Angebote für die Spiele
        game_ids = [game.id for game in games]
        game_ids_str = ','.join(str(game_id) for game_id in game_ids)

        query = f"""
        SELECT 
            game_id,
            streaming_package_id,
            live,
            highlights
        FROM streaming_offer
        WHERE game_id IN({game_ids_str})
        """

        offers = await self.db.execute(query, {"game_ids": game_ids})

        # Baue Coverage Map
        for package in packages:
            package_id = package['id']
            coverage_map[package_id] = {
                'games': [],
                'weighted_sum': 0
            }

            for game in games:
                game_offers = [
                    o for o in offers
                    if o['game_id'] == game.id and o['streaming_package_id'] == package_id
                ]

                for offer in game_offers:
                    # Prüfe, ob Angebot den Anforderungen entspricht
                    if require_live and not offer['live']:
                        continue

                    coverage_map[package_id]['games'].append(game)
                    coverage_map[package_id]['weighted_sum'] += game.total_weight
                    break  # Ein passendes Angebot reicht

        return coverage_map
