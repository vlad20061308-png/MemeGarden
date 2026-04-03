from __future__ import annotations

import time
from collections import defaultdict, deque


class AntiSpamService:
    def __init__(
        self,
        cooldown_seconds: float = 1.0,
        burst_limit: int = 4,
        min_interval_seconds: float = 0.2,
    ) -> None:
        self.cooldown_seconds = max(cooldown_seconds, 0.5)
        self.burst_limit = max(burst_limit, 2)
        self.min_interval_seconds = max(min_interval_seconds, 0.0)
        self._last_action: dict[int, float] = defaultdict(float)
        self._recent_actions: dict[int, deque[float]] = defaultdict(deque)

    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        if now - self._last_action[user_id] < self.min_interval_seconds:
            return False

        recent = self._recent_actions[user_id]
        while recent and now - recent[0] > self.cooldown_seconds:
            recent.popleft()

        if len(recent) >= self.burst_limit:
            return False

        recent.append(now)
        self._last_action[user_id] = now
        return True
