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



def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is not set. Create .env and add BOT_TOKEN=...")

    data_file = os.getenv("DATA_FILE", "app/data/game_state.json").strip()
    anti_spam_seconds = float(os.getenv("ANTI_SPAM_SECONDS", "1.0"))
    return Config(
        bot_token=token,
        data_file=data_file,
        anti_spam_seconds=anti_spam_seconds,
    )
