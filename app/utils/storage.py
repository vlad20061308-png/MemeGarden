from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from app.data.constants import DEFAULT_COINS
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
            farm = [PlantRecord(**item) for item in payload.get("farm", [])]
            self._data[user_id] = UserState(
                coins=payload.get("coins", DEFAULT_COINS),
                seeds=payload.get("seeds", {}),
                harvest=payload.get("harvest", {}),
                farm=farm,
            )

    def save(self) -> None:
        serializable: Dict[str, dict] = {}
        for user_id, state in self._data.items():
            serializable[user_id] = {
                "coins": state.coins,
                "seeds": state.seeds,
                "harvest": state.harvest,
                "farm": [
                    {
                        "seed_id": plant.seed_id,
                        "planted_at": plant.planted_at,
                        "grow_seconds": plant.grow_seconds,
                    }
                    for plant in state.farm
                ],
            }
        self.path.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_or_create_user(self, user_id: int) -> UserState:
        key = str(user_id)
        if key not in self._data:
            self._data[key] = UserState(coins=DEFAULT_COINS)
            self.save()
        return self._data[key]
