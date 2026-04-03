from __future__ import annotations

import time


def now_ts() -> float:
    return time.time()


def format_seconds(total_seconds: int) -> str:
    total_seconds = max(int(total_seconds), 0)
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}ч")
    if minutes:
        parts.append(f"{minutes}м")
    if seconds or not parts:
        parts.append(f"{seconds}с")
    return " ".join(parts)
