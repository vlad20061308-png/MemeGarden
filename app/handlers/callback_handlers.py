from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.deps import ANTISPAM_MESSAGE, get_game, is_allowed
from app.ui.cards import farm_card
from app.ui.keyboards import farm_keyboard


async def shop_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    seed_id = query.data.split(":", 1)[1]

    if not is_allowed(update, context):
        await query.edit_message_text(ANTISPAM_MESSAGE)
        return

    game = get_game(context)
    ok, message = game.buy_seed(update.effective_user.id, seed_id)
    prefix = "✅" if ok else "❌"
    await query.edit_message_text(f"{prefix} {message}")


async def plant_seed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    seed_id = query.data.split(":", 1)[1]

    if not is_allowed(update, context):
        await query.edit_message_text(ANTISPAM_MESSAGE)
        return

    game = get_game(context)
    ok, message = game.plant_seed(update.effective_user.id, seed_id)
    prefix = "✅" if ok else "❌"
    await query.edit_message_text(f"{prefix} {message}")


async def farm_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_allowed(update, context):
        await query.answer(ANTISPAM_MESSAGE, show_alert=False)
        return

    game = get_game(context)
    state = game.user(update.effective_user.id)
    await query.edit_message_text(farm_card(state), reply_markup=farm_keyboard())


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
