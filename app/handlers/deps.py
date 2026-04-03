from __future__ import annotations

import time

from telegram import Update
from telegram.ext import ContextTypes

from app.services.anti_spam import AntiSpamService
from app.services.game_service import GameService


ANTISPAM_MESSAGE = "⏳ Не так быстро."
ANTISPAM_MESSAGE_SOFT = "⏳ Чуть медленнее — действие пока на кулдауне."

ACTION_COOLDOWNS = {
    "command": 0.8,
    "callback_nav": 0.2,
    "callback_soft": 0.35,
    "callback_heavy": 0.8,
}
WARNING_COOLDOWN_SECONDS = 4.0


def get_game(context: ContextTypes.DEFAULT_TYPE) -> GameService:
    return context.application.bot_data["game"]


def get_antispam(context: ContextTypes.DEFAULT_TYPE) -> AntiSpamService:
    return context.application.bot_data["anti_spam"]


def is_dev_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    cfg = context.application.bot_data["config"]
    user = update.effective_user
    return bool(cfg.dev_mode and user and user.id in cfg.dev_user_ids)


def _rate_state(context: ContextTypes.DEFAULT_TYPE) -> dict:
    state = context.application.bot_data.get("ui_rate_state")
    if state is None:
        state = {"last_action": {}, "last_warning": {}}
        context.application.bot_data["ui_rate_state"] = state
    return state


def should_warn_antispam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if user is None:
        return False
    state = _rate_state(context)
    now = time.monotonic()
    last_warn = state["last_warning"].get(user.id, 0.0)
    if now - last_warn < WARNING_COOLDOWN_SECONDS:
        return False
    state["last_warning"][user.id] = now
    return True


def is_allowed(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str = "command") -> bool:
    user = update.effective_user
    if user is None:
        return False

    if action not in ACTION_COOLDOWNS:
        action = "command"

    state = _rate_state(context)
    now = time.monotonic()
    action_key = (user.id, action)
    action_cooldown = ACTION_COOLDOWNS[action]

    if now - state["last_action"].get(action_key, 0.0) < action_cooldown:
        return False

    if not get_antispam(context).is_allowed(user.id):
        return False

    state["last_action"][action_key] = now
    return True
