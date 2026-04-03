from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.deps import ANTISPAM_MESSAGE, get_game, is_allowed, is_dev_user
from app.ui.cards import (
    farm_card,
    format_level_reward_lines,
    help_card,
    inventory_card,
    level_card,
    shop_card,
)
from app.ui.keyboards import (
    dev_keyboard,
    farm_keyboard,
    inventory_keyboard,
    plant_keyboard,
    shop_keyboard,
)


def _format_dev_state(state: dict) -> str:
    lines = [
        "🛠 Developer state",
        f"user id: {state['user_id']}",
        f"DEV_MODE: {'on' if state['dev_mode'] else 'off'}",
        f"Баланс: {state['balance']}🪙",
        f"Активный инструмент: {state['active_tool']}",
        f"Семян: {state['seeds_count']}",
        f"Растений: {state['plants_count']}",
        f"Level/XP: {state['level']} / {state['xp']}",
    ]
    if not state["plants"]:
        lines.append("Растения: (пусто)")
    else:
        lines.append("Растения:")
        for plant in state["plants"]:
            lines.append(
                f"- #{plant['plant_id']} | {plant['state']} | due_at={plant['due_at']} | wilt_at={plant['wilt_at']}"
            )
    return "\n".join(lines)


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
    xp = result["xp"]
    lines = [
        f"Собрано: {result['harvested']}",
        f"Засохло и удалено: {result['wilted']}",
        f"Не собрано из-за лимита инвентаря: {result['blocked']}",
        f"Дроп: {drops}",
        f"Получено монет: {result['coins']}🪙",
        f"Получено XP: +{xp['xp_added']} (всего: {xp['xp_total']})",
    ]
    if xp["leveled_up"]:
        lines.append(f"🎉 Уровень: {xp['old_level']} → {xp['new_level']}")
        rewards_block = format_level_reward_lines(xp["granted_rewards"])
        if rewards_block:
            lines.append(rewards_block)

    await update.message.reply_text("\n".join(lines))


async def inventory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    state = game.user(update.effective_user.id)
    await update.message.reply_text(inventory_card(state), reply_markup=inventory_keyboard(state))


async def level_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    state = game.user(update.effective_user.id)
    progress = game.get_level_progress(update.effective_user.id)
    await update.message.reply_text(level_card(state, progress))


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update, context):
        await update.message.reply_text(ANTISPAM_MESSAGE)
        return
    game = get_game(context)
    state = game.user(update.effective_user.id)
    await update.message.reply_text(f"Баланс: {state.coins}🪙")


async def dev_ready_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_dev_user(update, context):
        await update.message.reply_text("Недостаточно прав")
        return
    game = get_game(context)
    _, message = game.force_ready_all(update.effective_user.id)
    await update.message.reply_text(f"✅ {message}")


async def dev_ready_one_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_dev_user(update, context):
        await update.message.reply_text("Недостаточно прав")
        return
    if not context.args:
        await update.message.reply_text("Использование: /dev_ready_one <plant_id>")
        return
    try:
        plant_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("plant_id должен быть числом.")
        return
    game = get_game(context)
    ok, message = game.force_ready_one(update.effective_user.id, plant_id)
    await update.message.reply_text(("✅ " if ok else "❌ ") + message)


async def dev_wilt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_dev_user(update, context):
        await update.message.reply_text("Недостаточно прав")
        return
    game = get_game(context)
    _, message = game.force_wilt_all(update.effective_user.id)
    await update.message.reply_text(f"✅ {message}")


async def dev_balance_set_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_dev_user(update, context):
        await update.message.reply_text("Недостаточно прав")
        return
    if not context.args:
        await update.message.reply_text("Использование: /dev_balance_set <amount>")
        return
    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("amount должен быть числом.")
        return
    game = get_game(context)
    ok, message = game.set_balance(update.effective_user.id, amount)
    await update.message.reply_text(("✅ " if ok else "❌ ") + message)


async def dev_balance_add_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_dev_user(update, context):
        await update.message.reply_text("Недостаточно прав")
        return
    if not context.args:
        await update.message.reply_text("Использование: /dev_balance_add <amount>")
        return
    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("amount должен быть числом.")
        return
    game = get_game(context)
    ok, message = game.add_balance(update.effective_user.id, amount)
    await update.message.reply_text(("✅ " if ok else "❌ ") + message)


async def dev_balance_take_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_dev_user(update, context):
        await update.message.reply_text("Недостаточно прав")
        return
    if not context.args:
        await update.message.reply_text("Использование: /dev_balance_take <amount>")
        return
    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("amount должен быть числом.")
        return
    game = get_game(context)
    ok, message = game.take_balance(update.effective_user.id, amount)
    await update.message.reply_text(("✅ " if ok else "❌ ") + message)


async def dev_state_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_dev_user(update, context):
        await update.message.reply_text("Недостаточно прав")
        return
    cfg = context.application.bot_data["config"]
    game = get_game(context)
    state = game.get_dev_state(update.effective_user.id, cfg.dev_mode)
    await update.message.reply_text(_format_dev_state(state), reply_markup=dev_keyboard())
