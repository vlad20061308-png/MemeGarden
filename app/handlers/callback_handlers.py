from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.deps import ANTISPAM_MESSAGE, get_game, is_allowed, is_dev_user
from app.ui.cards import farm_card, inventory_card
from app.ui.keyboards import dev_keyboard, farm_keyboard, inventory_keyboard


def _format_dev_state(state: dict) -> str:
    lines = [
        "🛠 Developer state",
        f"user id: {state['user_id']}",
        f"DEV_MODE: {'on' if state['dev_mode'] else 'off'}",
        f"Баланс: {state['balance']}🪙",
        f"Активный инструмент: {state['active_tool']}",
        f"Семян: {state['seeds_count']}",
        f"Растений: {state['plants_count']}",
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


async def shop_buy_seed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def shop_buy_tool_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    tool_id = query.data.split(":", 1)[1]

    if not is_allowed(update, context):
        await query.edit_message_text(ANTISPAM_MESSAGE)
        return

    game = get_game(context)
    ok, message = game.buy_tool(update.effective_user.id, tool_id)
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
    farm_rows = game.get_farm_view(update.effective_user.id)
    await query.edit_message_text(
        farm_card(farm_rows),
        reply_markup=farm_keyboard([row["plant_id"] for row in farm_rows]),
    )


async def farm_harvest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_allowed(update, context):
        await query.answer(ANTISPAM_MESSAGE, show_alert=False)
        return

    game = get_game(context)
    result = game.harvest(update.effective_user.id)
    await query.edit_message_text(
        f"🧺 Собрано: {result['harvested']} | Засохло: {result['wilted']} | Блок по лимиту: {result['blocked']}\n"
        f"Монеты: +{result['coins']}🪙"
    )


async def farm_boost_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    plant_id = int(query.data.split(":", 1)[1])

    if not is_allowed(update, context):
        await query.answer(ANTISPAM_MESSAGE, show_alert=False)
        return

    game = get_game(context)
    ok, message = game.boost_plant(update.effective_user.id, plant_id)
    await query.answer(("✅ " if ok else "❌ ") + message, show_alert=False)

    farm_rows = game.get_farm_view(update.effective_user.id)
    await query.edit_message_text(
        farm_card(farm_rows),
        reply_markup=farm_keyboard([row["plant_id"] for row in farm_rows]),
    )


async def equip_tool_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    tool_id = query.data.split(":", 1)[1]

    if not is_allowed(update, context):
        await query.answer(ANTISPAM_MESSAGE, show_alert=False)
        return

    game = get_game(context)
    ok, message = game.equip_tool(update.effective_user.id, tool_id)
    await query.answer(("✅ " if ok else "❌ ") + message, show_alert=False)

    state = game.user(update.effective_user.id)
    await query.edit_message_text(inventory_card(state), reply_markup=inventory_keyboard(state))


async def drop_item_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item_id = query.data.split(":", 1)[1]

    if not is_allowed(update, context):
        await query.answer(ANTISPAM_MESSAGE, show_alert=False)
        return

    game = get_game(context)
    ok, message = game.drop_one_item(update.effective_user.id, item_id)
    await query.answer(("✅ " if ok else "❌ ") + message, show_alert=False)

    state = game.user(update.effective_user.id)
    await query.edit_message_text(inventory_card(state), reply_markup=inventory_keyboard(state))


async def menu_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⬅️ Вернись в меню командами: /shop /plant /farm /inventory")


async def shop_section_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("Используй кнопки ниже для покупки.", show_alert=False)


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()


async def dev_ready_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not is_dev_user(update, context):
        await query.answer("Недостаточно прав", show_alert=False)
        return
    game = get_game(context)
    _, message = game.force_ready_all(update.effective_user.id)
    cfg = context.application.bot_data["config"]
    state = game.get_dev_state(update.effective_user.id, cfg.dev_mode)
    await query.edit_message_text(f"✅ {message}\n\n{_format_dev_state(state)}", reply_markup=dev_keyboard())


async def dev_wilt_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not is_dev_user(update, context):
        await query.answer("Недостаточно прав", show_alert=False)
        return
    game = get_game(context)
    _, message = game.force_wilt_all(update.effective_user.id)
    cfg = context.application.bot_data["config"]
    state = game.get_dev_state(update.effective_user.id, cfg.dev_mode)
    await query.edit_message_text(f"✅ {message}\n\n{_format_dev_state(state)}", reply_markup=dev_keyboard())


async def dev_add_1000_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not is_dev_user(update, context):
        await query.answer("Недостаточно прав", show_alert=False)
        return
    game = get_game(context)
    _, message = game.add_balance(update.effective_user.id, 1000)
    cfg = context.application.bot_data["config"]
    state = game.get_dev_state(update.effective_user.id, cfg.dev_mode)
    await query.edit_message_text(f"✅ {message}\n\n{_format_dev_state(state)}", reply_markup=dev_keyboard())


async def dev_set_100000_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not is_dev_user(update, context):
        await query.answer("Недостаточно прав", show_alert=False)
        return
    game = get_game(context)
    _, message = game.set_balance(update.effective_user.id, 100000)
    cfg = context.application.bot_data["config"]
    state = game.get_dev_state(update.effective_user.id, cfg.dev_mode)
    await query.edit_message_text(f"✅ {message}\n\n{_format_dev_state(state)}", reply_markup=dev_keyboard())


async def dev_state_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not is_dev_user(update, context):
        await query.answer("Недостаточно прав", show_alert=False)
        return
    cfg = context.application.bot_data["config"]
    game = get_game(context)
    state = game.get_dev_state(update.effective_user.id, cfg.dev_mode)
    await query.edit_message_text(_format_dev_state(state), reply_markup=dev_keyboard())
