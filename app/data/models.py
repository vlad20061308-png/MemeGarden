from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PlantRecord:
    seed_id: str
    planted_at: float
    grow_seconds: int


@dataclass
class UserState:
    coins: int
    seeds: Dict[str, int] = field(default_factory=dict)
    harvest: Dict[str, int] = field(default_factory=dict)
    farm: List[PlantRecord] = field(default_factory=list)
