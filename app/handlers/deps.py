from __future__ import annotations

import time

from telegram import Update
from telegram.ext import ContextTypes

from app.services.anti_spam import AntiSpamService
from app.services.game_service import GameService


ANTISPAM_MESSAGE_SOFT = "⏳ Подожди немного... действие ещё на кулдауне."

ACTION_COOLDOWNS = {
    "command": 0.7,
    "callback_nav": 0.15,
    "callback_soft": 0.25,
    "callback_heavy": 0.65,
}
WARNING_COOLDOWN_SECONDS = 6.0


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
    blocks = state["blocked_count"].get(user.id, 0)
    if action == "callback_soft" and blocks % 3 != 0:
        return False
    if action in {"command", "callback_heavy"} and blocks % 2 != 0:
        return False

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

    is_limited = now - state["last_action"].get(action_key, 0.0) < action_cooldown
    if not is_limited and action in {"command", "callback_heavy"}:
        is_limited = not get_antispam(context).is_allowed(user.id)

    if is_limited:
        state["blocked_count"][user.id] = state["blocked_count"].get(user.id, 0) + 1
        return False

    state["last_action"][action_key] = now
    state["blocked_count"][user.id] = 0
    return True
