from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.deps import ANTISPAM_MESSAGE, get_game, is_allowed
from app.ui.cards import farm_card, help_card, inventory_card, shop_card
from app.ui.keyboards import farm_keyboard, inventory_keyboard, plant_keyboard, shop_keyboard


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    game.user(update.effective_user.id)
    await update.message.reply_text(
        "Добро пожаловать в MemeGarden! Старт: 10🪙, покупай семена в /shop и сажай через /plant."
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    await update.message.reply_text(help_card())


async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    await update.message.reply_text(shop_card(), reply_markup=shop_keyboard())


async def plant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    state = game.user(update.effective_user.id)
    await update.message.reply_text(
        "Выбери купленное семя для посадки:", reply_markup=plant_keyboard(state.seeds)
    )


async def farm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    farm_rows = game.get_farm_view(update.effective_user.id)
    await update.message.reply_text(
        farm_card(farm_rows),
        reply_markup=farm_keyboard([row["plant_id"] for row in farm_rows]),
    )


async def harvest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    result = game.harvest(update.effective_user.id)
    if result["harvested"] == 0 and result["wilted"] == 0:
        await update.message.reply_text("Пока нечего собирать. Проверь /farm")
        return

    drops = ", ".join(result["drops"]) if result["drops"] else "—"
    await update.message.reply_text(
        f"Собрано: {result['harvested']}\n"
        f"Засохло и удалено: {result['wilted']}\n"
        f"Не собрано из-за лимита инвентаря: {result['blocked']}\n"
        f"Дроп: {drops}\n"
        f"Получено монет: {result['coins']}🪙"
    )


async def inventory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    state = game.user(update.effective_user.id)
    await update.message.reply_text(inventory_card(state), reply_markup=inventory_keyboard(state))


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    state = game.user(update.effective_user.id)
    await update.message.reply_text(f"Баланс: {state.coins}🪙")
