from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


async def shop_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    seed_id = query.data.split(":", 1)[1]

    anti_spam = context.application.bot_data["anti_spam"]
    if not anti_spam.is_allowed(update.effective_user.id):
        await query.edit_message_text("⏳ Не так быстро.")
        return

    game = context.application.bot_data["game"]
    ok, message = game.buy_seed(update.effective_user.id, seed_id)
    prefix = "✅" if ok else "❌"
    await query.edit_message_text(f"{prefix} {message}")


async def plant_seed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    seed_id = query.data.split(":", 1)[1]

    anti_spam = context.application.bot_data["anti_spam"]
    if not anti_spam.is_allowed(update.effective_user.id):
        await query.edit_message_text("⏳ Не так быстро.")
        return

    game = context.application.bot_data["game"]
    ok, message = game.plant_seed(update.effective_user.id, seed_id)
    prefix = "✅" if ok else "❌"
    await query.edit_message_text(f"{prefix} {message}")


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
