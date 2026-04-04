from __future__ import annotations

import time

from telegram import Update
from telegram.ext import ContextTypes

from app.services.anti_spam import AntiSpamService
from app.services.game_service import GameService


ANTISPAM_MESSAGE_SOFT = "⏳ Подожди немного..."

ACTION_COOLDOWNS = {
    "command": 1.0,
    "callback_nav": 0.12,
    "callback_soft": 0.22,
    "callback_heavy": 0.55,
}
WARNING_COOLDOWN_SECONDS = {
    "command": 8.0,
    "callback_soft": 12.0,
    "callback_heavy": 7.0,
}


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
        state = {"last_action": {}, "last_warning": {}, "blocked_count": {}}
        context.application.bot_data["ui_rate_state"] = state
    return state


def should_warn_antispam(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str = "command") -> bool:
    user = update.effective_user
    if user is None or action == "callback_nav":
        return False

    state = _rate_state(context)
    blocks = state["blocked_count"].get((user.id, action), 0)

    if action == "callback_soft" and blocks < 4:
        return False
    if action in {"command", "callback_heavy"} and blocks < 2:
        return False

    now = time.monotonic()
    warn_key = (user.id, action)
    warning_cooldown = WARNING_COOLDOWN_SECONDS.get(action, 8.0)
    last_warn = state["last_warning"].get(warn_key, 0.0)
    if now - last_warn < warning_cooldown:
        return False

    state["last_warning"][warn_key] = now
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

    is_limited = now - state["last_action"].get(action_key, 0.0) < action_cooldown
    if not is_limited and action in {"command", "callback_heavy"}:
        is_limited = not get_antispam(context).is_allowed(user.id)

    if is_limited:
        block_key = (user.id, action)
        state["blocked_count"][block_key] = state["blocked_count"].get(block_key, 0) + 1
        return False

    state["last_action"][action_key] = now
    state["blocked_count"][(user.id, action)] = 0
    return True
