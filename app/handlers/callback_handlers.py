from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.deps import (
    ANTISPAM_MESSAGE_SOFT,
    get_game,
    is_allowed,
    is_dev_user,
    should_warn_antispam,
)
from app.ui.cards import (
    farm_card,
    format_level_reward_lines,
    inventory_card,
    level_card,
    menu_hint_card,
    shop_card,
    tools_card,
)
from app.ui.keyboards import (
    dev_keyboard,
    farm_keyboard,
    inventory_keyboard,
    main_menu_keyboard,
    plant_keyboard,
    shop_menu_keyboard,
    shop_seeds_keyboard,
    shop_tools_keyboard,
)

UNAVAILABLE_MESSAGES = {
    "boost": "⚡ Сейчас ускорение недоступно. Подожди откат или найди растущее растение.",
    "harvest": "🌾 Пока нечего собирать. Дай растениям созреть.",
    "plant": "🪴 Посадка недоступна: проверь семена и свободные слоты.",
    "inventory": "🎒 Сейчас это действие недоступно.",
}


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


async def _render_farm(query, game, user_id: int) -> None:
    farm_state = game.get_farm_action_state(user_id)
    await query.edit_message_text(
        farm_card(farm_state["farm_rows"], farm_state),
        reply_markup=farm_keyboard(farm_state),
    )


async def _render_inventory(query, game, user_id: int, card_builder=inventory_card) -> None:
    state = game.user(user_id)
    farm_state = game.get_farm_action_state(user_id)
    await query.edit_message_text(
        card_builder(state),
        reply_markup=inventory_keyboard(
            state,
            has_seeds=farm_state["has_seeds"] and farm_state["free_slots"] > 0,
            has_drops=farm_state["has_inventory_items"],
        ),
    )


async def shop_buy_seed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    seed_id = query.data.split(":", 1)[1]

    if not is_allowed(update, context, action="callback_heavy"):
        if should_warn_antispam(update, context, action="callback_heavy"):
            await query.answer(ANTISPAM_MESSAGE_SOFT, show_alert=False)
        return

    game = get_game(context)
    ok, message = game.buy_seed(update.effective_user.id, seed_id)
    prefix = "✅" if ok else "❌"
    await query.edit_message_text(f"{prefix} {message}", reply_markup=shop_seeds_keyboard())


async def shop_buy_tool_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    tool_id = query.data.split(":", 1)[1]

    if not is_allowed(update, context, action="callback_heavy"):
        if should_warn_antispam(update, context, action="callback_heavy"):
            await query.answer(ANTISPAM_MESSAGE_SOFT, show_alert=False)
        return

    game = get_game(context)
    ok, message = game.buy_tool(update.effective_user.id, tool_id)
    prefix = "✅" if ok else "❌"
    await query.edit_message_text(f"{prefix} {message}", reply_markup=shop_tools_keyboard())


async def plant_seed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    seed_id = query.data.split(":", 1)[1]

    if not is_allowed(update, context, action="callback_heavy"):
        if should_warn_antispam(update, context, action="callback_heavy"):
            await query.answer(ANTISPAM_MESSAGE_SOFT, show_alert=False)
        return

    game = get_game(context)
    ok, message = game.plant_seed(update.effective_user.id, seed_id)
    prefix = "✅" if ok else "❌"
    state = game.user(update.effective_user.id)
    farm_state = game.get_farm_action_state(update.effective_user.id)
    await query.edit_message_text(
        f"{prefix} {message}",
        reply_markup=plant_keyboard(state.seeds, can_plant=farm_state["can_plant"]),
    )


async def farm_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_allowed(update, context, action="callback_soft"):
        if should_warn_antispam(update, context, action="callback_soft"):
            await query.answer(ANTISPAM_MESSAGE_SOFT, show_alert=False)
        return

    game = get_game(context)
    await _render_farm(query, game, update.effective_user.id)


async def farm_harvest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_allowed(update, context, action="callback_heavy"):
        if should_warn_antispam(update, context, action="callback_heavy"):
            await query.answer(ANTISPAM_MESSAGE_SOFT, show_alert=False)
        return

    game = get_game(context)
    result = game.harvest(update.effective_user.id)
    xp = result["xp"]
    lines = [
        f"🧺 Собрано: {result['harvested']} | Засохло: {result['wilted']} | Блок по лимиту: {result['blocked']}",
        f"Монеты: +{result['coins']}🪙",
        f"XP: +{xp['xp_added']} (всего: {xp['xp_total']})",
    ]
    if xp["leveled_up"]:
        lines.append(f"🎉 Уровень: {xp['old_level']} → {xp['new_level']}")
        rewards_block = format_level_reward_lines(xp["granted_rewards"])
        if rewards_block:
            lines.append(rewards_block)

    await query.edit_message_text("\n".join(lines), reply_markup=main_menu_keyboard())


async def farm_boost_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    plant_id = int(query.data.split(":", 1)[1])

    if not is_allowed(update, context, action="callback_heavy"):
        if should_warn_antispam(update, context, action="callback_heavy"):
            await query.answer(ANTISPAM_MESSAGE_SOFT, show_alert=False)
        return

    game = get_game(context)
    ok, message = game.boost_plant(update.effective_user.id, plant_id)
    await query.answer(("✅ " if ok else "❌ ") + message, show_alert=False)
    await _render_farm(query, game, update.effective_user.id)


async def equip_tool_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    tool_id = query.data.split(":", 1)[1]

    if not is_allowed(update, context, action="callback_heavy"):
        if should_warn_antispam(update, context, action="callback_heavy"):
            await query.answer(ANTISPAM_MESSAGE_SOFT, show_alert=False)
        return

    game = get_game(context)
    ok, message = game.equip_tool(update.effective_user.id, tool_id)
    await query.answer(("✅ " if ok else "❌ ") + message, show_alert=False)
    await _render_inventory(query, game, update.effective_user.id)


async def drop_item_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item_id = query.data.split(":", 1)[1]

    if not is_allowed(update, context, action="callback_heavy"):
        if should_warn_antispam(update, context, action="callback_heavy"):
            await query.answer(ANTISPAM_MESSAGE_SOFT, show_alert=False)
        return

    game = get_game(context)
    ok, message = game.drop_one_item(update.effective_user.id, item_id)
    await query.answer(("✅ " if ok else "❌ ") + message, show_alert=False)
    await _render_inventory(query, game, update.effective_user.id)


async def menu_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    game = get_game(context)
    hub = game.get_hub_state(update.effective_user.id)
    await query.edit_message_text(menu_hint_card(hub), reply_markup=main_menu_keyboard())


async def shop_section_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    section = query.data.split(":", 1)[1]
    if not is_allowed(update, context, action="callback_nav"):
        return
    if section == "seeds":
        await query.edit_message_text("🌱 Раздел семян", reply_markup=shop_seeds_keyboard())
        return
    if section == "tools":
        await query.edit_message_text("🛠 Раздел инструментов", reply_markup=shop_tools_keyboard())
        return
    await query.answer("Раздел не найден", show_alert=False)


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()


async def unavailable_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    reason = query.data.split(":", 1)[1]
    await query.answer(UNAVAILABLE_MESSAGES.get(reason, "⏳ Это действие сейчас недоступно."), show_alert=False)


async def menu_open_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    target = query.data.split(":", 1)[1]

    action = "callback_nav"
    if target in {"harvest", "plant"}:
        action = "callback_heavy"
    elif target in {"farm", "refresh", "inventory", "tools", "profile", "shop"}:
        action = "callback_soft"

    if not is_allowed(update, context, action=action):
        if should_warn_antispam(update, context, action=action):
            await query.answer(ANTISPAM_MESSAGE_SOFT, show_alert=False)
        return

    game = get_game(context)
    user_id = update.effective_user.id

    if target == "shop":
        await query.edit_message_text(shop_card(), reply_markup=shop_menu_keyboard())
        return
    if target == "farm" or target == "refresh":
        await _render_farm(query, game, user_id)
        return
    if target == "inventory":
        await _render_inventory(query, game, user_id)
        return
    if target == "tools":
        await _render_inventory(query, game, user_id, card_builder=tools_card)
        return
    if target == "plant":
        state = game.user(user_id)
        farm_state = game.get_farm_action_state(user_id)
        await query.edit_message_text(
            "🪴 Выбери семя для посадки",
            reply_markup=plant_keyboard(state.seeds, can_plant=farm_state["can_plant"]),
        )
        return
    if target == "harvest":
        result = game.harvest(user_id)
        xp = result["xp"]
        lines = [
            f"🧺 Собрано: {result['harvested']} | Засохло: {result['wilted']} | Блок по лимиту: {result['blocked']}",
            f"Монеты: +{result['coins']}🪙",
            f"XP: +{xp['xp_added']} (всего: {xp['xp_total']})",
        ]
        await query.edit_message_text("\n".join(lines), reply_markup=main_menu_keyboard())
        return
    if target == "profile":
        state = game.user(user_id)
        progress = game.get_level_progress(user_id)
        await query.edit_message_text(level_card(state, progress), reply_markup=main_menu_keyboard())
        return
    await query.answer("Раздел пока недоступен", show_alert=False)


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
