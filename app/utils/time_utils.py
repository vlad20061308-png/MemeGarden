from __future__ import annotations

import time


def now_ts() -> float:
    return time.time()


def format_seconds(total_seconds: int) -> str:
    minutes, seconds = divmod(max(total_seconds, 0), 60)
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"
