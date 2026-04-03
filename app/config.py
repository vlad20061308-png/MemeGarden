from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    data_file: str = "app/data/game_state.json"
    anti_spam_seconds: float = 1.0



def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is not set. Create a .env file and add BOT_TOKEN=... ")
    return Config(bot_token=token)
