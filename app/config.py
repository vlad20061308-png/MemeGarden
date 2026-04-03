from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"

load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class Config:
    bot_token: str
    data_file: str
    anti_spam_seconds: float
    dev_mode: bool
    dev_user_ids: frozenset[int]



def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is not set. Create .env and add BOT_TOKEN=...")

    data_file = os.getenv("DATA_FILE", "app/data/game_state.json").strip()
    anti_spam_seconds = float(os.getenv("ANTI_SPAM_SECONDS", "1.0"))
    dev_mode = os.getenv("DEV_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
    raw_dev_ids = os.getenv("DEV_USER_IDS", "").strip()
    dev_user_ids: set[int] = set()
    if raw_dev_ids:
        for chunk in raw_dev_ids.split(","):
            value = chunk.strip()
            if not value:
                continue
            dev_user_ids.add(int(value))
    return Config(
        bot_token=token,
        data_file=data_file,
        anti_spam_seconds=anti_spam_seconds,
        dev_mode=dev_mode,
        dev_user_ids=frozenset(dev_user_ids),
    )
