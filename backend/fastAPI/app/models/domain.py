from pydantic import BaseModel
from datetime import datetime


class Game(BaseModel):
    id: int
    team_home: str
    team_away: str
    tournament: str
    starts_at: datetime
    base_weight: float
    phase_multiplier: float
    importance_multiplier: float

    @property
    def total_weight(self) -> float:
        return self.base_weight * self.phase_multiplier * self.importance_multiplier
