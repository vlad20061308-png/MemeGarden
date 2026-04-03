from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.deps import ANTISPAM_MESSAGE, get_game, is_allowed
from app.ui.cards import farm_card, help_card, inventory_card, shop_card
from app.ui.keyboards import farm_keyboard, plant_keyboard, shop_keyboard


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    game.user(update.effective_user.id)
    await update.message.reply_text(
        "Добро пожаловать в MemeGarden! Используй /help для списка команд."
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
        "Выбери семя для посадки:", reply_markup=plant_keyboard(state.seeds)
    )


async def farm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    state = game.user(update.effective_user.id)
    await update.message.reply_text(farm_card(state), reply_markup=farm_keyboard())


async def harvest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    count, coins = game.harvest(update.effective_user.id)
    if count == 0:
        await update.message.reply_text("Пока нечего собирать. Проверь /farm")
        return
    await update.message.reply_text(f"Собрано растений: {count}. Получено {coins}🪙")


async def inventory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    state = game.user(update.effective_user.id)
    await update.message.reply_text(inventory_card(state))


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    state = game.user(update.effective_user.id)
    await update.message.reply_text(f"Баланс: {state.coins}🪙")
