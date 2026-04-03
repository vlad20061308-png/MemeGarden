from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.services.anti_spam import AntiSpamService
from app.services.game_service import GameService


ANTISPAM_MESSAGE = "⏳ Не так быстро."


def get_game(context: ContextTypes.DEFAULT_TYPE) -> GameService:
    return context.application.bot_data["game"]


def get_antispam(context: ContextTypes.DEFAULT_TYPE) -> AntiSpamService:
    return context.application.bot_data["anti_spam"]


def is_dev_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    cfg = context.application.bot_data["config"]
    user = update.effective_user
    return bool(cfg.dev_mode and user and user.id in cfg.dev_user_ids)


def is_allowed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if user is None:
        return False
    return get_antispam(context).is_allowed(user.id)
