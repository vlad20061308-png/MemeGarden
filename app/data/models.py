from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PlantRecord:
    plant_id: int
    seed_id: str
    tree_id: str
    planted_at: float
    due_at: float
    wilt_at: float
    grow_seconds: int
    ready_window_seconds: int
    boost_clicks_used: int = 0
    boost_last_at: float = 0.0


@dataclass
class UserState:
    coins: int
    seeds: Dict[str, int] = field(default_factory=dict)
    harvest: Dict[str, int] = field(default_factory=dict)
    farm: List[PlantRecord] = field(default_factory=list)
    owned_tools: Dict[str, int] = field(default_factory=dict)
    active_tool: Optional[str] = None
    inventory_capacity: int = 6
    next_plant_id: int = 1
