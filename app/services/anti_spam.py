from __future__ import annotations

import time
from collections import defaultdict


class AntiSpamService:
    def __init__(self, cooldown_seconds: float = 1.0) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._last_action: dict[int, float] = defaultdict(float)

    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        if now - self._last_action[user_id] < self.cooldown_seconds:
            return False
        self._last_action[user_id] = now
        return True
