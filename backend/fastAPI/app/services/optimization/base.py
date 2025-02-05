from abc import ABC, abstractmethod
from typing import List, Dict
from ...models.domain import Game


class PackageOptimizer(ABC):
    """Base class für verschiedene Optimierungsstrategien."""

    @abstractmethod
    async def optimize(
            self,
            games: List[Game],
            packages: List[Dict],
            coverage_map: Dict,
            max_packages: int
    ) -> Dict:
        pass

