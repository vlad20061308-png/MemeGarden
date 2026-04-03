from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from app.data.constants import DEFAULT_COINS, DEFAULT_INVENTORY_CAPACITY
from app.data.models import PlantRecord, UserState


class Storage:
    """JSON storage backend for game state."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, UserState] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        for user_id, payload in raw.items():
            farm: list[PlantRecord] = []
            for item in payload.get("farm", []):
                plant_id = item.get("plant_id")
                if plant_id is None:
                    # backward compatibility with old farm entries
                    plant_id = len(farm) + 1
                    planted_at = item["planted_at"]
                    grow_seconds = int(item.get("grow_seconds", 60))
                    due_at = item.get("due_at", planted_at + grow_seconds)
                    farm.append(
                        PlantRecord(
                            plant_id=plant_id,
                            seed_id=item["seed_id"],
                            tree_id=item.get("tree_id", "apple"),
                            planted_at=planted_at,
                            due_at=due_at,
                            wilt_at=item.get("wilt_at", due_at + max(600, grow_seconds // 2)),
                            grow_seconds=grow_seconds,
                            ready_window_seconds=item.get(
                                "ready_window_seconds", max(600, grow_seconds // 2)
                            ),
                            boost_clicks_used=item.get("boost_clicks_used", 0),
                            boost_last_at=item.get("boost_last_at", 0.0),
                        )
                    )
                    continue

                farm.append(PlantRecord(**item))

            self._data[user_id] = UserState(
                coins=payload.get("coins", DEFAULT_COINS),
                seeds=payload.get("seeds", {}),
                harvest=payload.get("harvest", {}),
                farm=farm,
                owned_tools=payload.get("owned_tools", {}),
                active_tool=payload.get("active_tool"),
                inventory_capacity=payload.get("inventory_capacity", DEFAULT_INVENTORY_CAPACITY),
                next_plant_id=payload.get("next_plant_id", len(farm) + 1),
            )

    def save(self) -> None:
        serializable: Dict[str, dict] = {}
        for user_id, state in self._data.items():
            serializable[user_id] = {
                "coins": state.coins,
                "seeds": state.seeds,
                "harvest": state.harvest,
                "farm": [plant.__dict__ for plant in state.farm],
                "owned_tools": state.owned_tools,
                "active_tool": state.active_tool,
                "inventory_capacity": state.inventory_capacity,
                "next_plant_id": state.next_plant_id,
            }
        self.path.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_or_create_user(self, user_id: int) -> UserState:
        key = str(user_id)
        if key not in self._data:
            self._data[key] = UserState(
                coins=DEFAULT_COINS,
                inventory_capacity=DEFAULT_INVENTORY_CAPACITY,
            )
            self.save()
        return self._data[key]
