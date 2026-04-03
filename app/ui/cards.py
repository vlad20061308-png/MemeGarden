from __future__ import annotations

from app.data.constants import (
    INVENTORY_CAPACITY_LEVELS,
    MAX_FARM_SLOTS,
    MAX_LEVEL,
    SEED_TYPES,
    STATE_GROWING,
    STATE_READY,
    STATE_WILTED,
    TOOLS,
)
from app.data.models import UserState
from app.utils.time_utils import format_seconds


def start_card(state: UserState) -> str:
    return (
        "🌿 MemeGarden\n"
        "Твоя мини-ферма редких мемных деревьев.\n\n"
        "✨ Что делать:\n"
        "• покупай семена в магазине\n"
        "• сажай и ускоряй рост\n"
        "• собирай дропы и монеты\n\n"
        f"💰 Баланс: {state.coins}🪙\n"
        f"📈 Уровень: {state.level} | XP: {state.xp}\n"
        f"🌱 Семян: {sum(state.seeds.values())} | 🌳 На ферме: {len(state.farm)}"
    )


def menu_hint_card() -> str:
    return (
        "🏠 Главное меню\n"
        "Выбери действие кнопками ниже.\n"
        "Команды тоже работают: /farm /shop /inventory /level."
    )


def format_level_reward_lines(granted_rewards: list[dict]) -> str:
    if not granted_rewards:
        return ""

    lines = ["🎁 Награды за уровень:"]
    for reward in granted_rewards:
        parts = [f"lvl {reward['level']}"]
        if reward.get("coins", 0) > 0:
            parts.append(f"+{reward['coins']}🪙")

        seeds = reward.get("seeds", {})
        if seeds:
            seed_text = ", ".join(f"{SEED_TYPES.get(seed_id, {'title': seed_id})['title']} x{amount}" for seed_id, amount in seeds.items())
            parts.append(seed_text)

        tools = reward.get("tools", {})
        if tools:
            tool_text = ", ".join(
                f"{TOOLS.get(tool_id, {'title': tool_id})['title']} x{amount}" for tool_id, amount in tools.items()
            )
            parts.append(tool_text)

        if reward.get("inventory_capacity_bonus", 0) > 0:
            parts.append(f"+{reward['inventory_capacity_bonus']} к лимиту инвентаря")

        lines.append("- " + " | ".join(parts))

    return "\n".join(lines)


def help_card() -> str:
    return (
        "ℹ️ Команды MemeGarden\n"
        "• /start • /help • /shop • /plant • /farm\n"
        "• /harvest • /inventory • /balance • /level\n\n"
        "🛠 Dev:\n"
        "/dev_ready, /dev_ready_one, /dev_wilt,\n"
        "/dev_balance_set, /dev_balance_add, /dev_balance_take, /dev_state"
    )


def shop_card() -> str:
    lines = ["🛒 Магазин MemeGarden", "Выбери раздел кнопками ниже.", "", "🌱 Семена:"]
    for data in SEED_TYPES.values():
        lines.append(f"- {data['title']}: {data['price']}🪙")

    lines.extend(["", "🛠 Инструменты (ускоряют рост при посадке):"])
    for data in TOOLS.values():
        lines.append(f"- {data['title']}: {data['price']}🪙 (−{data['reduction_pct']}%)")
    return "\n".join(lines)


def level_card(state: UserState, level_progress: dict) -> str:
    next_level = level_progress["next_level"]
    if next_level is None:
        progress_line = f"🏆 Достигнут максимальный уровень: {MAX_LEVEL}"
    else:
        progress_line = (
            f"До уровня {next_level}: {level_progress['xp_to_next']} XP"
            f" (порог: {level_progress['next_level_xp']} XP)"
        )

    return (
        "👤 Профиль игрока\n"
        "────────────\n"
        f"📈 Уровень: {state.level}\n"
        f"✨ XP: {state.xp}\n"
        f"➡️ {progress_line}\n"
        f"🎁 Получено наград уровней: {len(state.claimed_level_rewards)}"
    )


def _progress_bar(progress: float, width: int = 10) -> str:
    filled = int(progress * width)
    return "🟩" * filled + "⬜" * (width - filled)


def farm_card(farm_rows: list[dict]) -> str:
    lines = [f"🌱 Ферма {len(farm_rows)}/{MAX_FARM_SLOTS}", "────────────"]
    if not farm_rows:
        lines.append("Пусто. Нажми «Посадить» и начни выращивать.")

    for idx, row in enumerate(farm_rows, start=1):
        if row["state"] == STATE_GROWING:
            state_line = f"⏳ Растёт: {format_seconds(row['time_left'])}"
        elif row["state"] == STATE_READY:
            state_line = "✅ Готово к сбору"
        else:
            state_line = "🥀 Засохло (нужно убрать через /harvest)"

        if row["state"] == STATE_GROWING:
            if row["next_boost_in"] > 0:
                next_boost = f"через {format_seconds(row['next_boost_in'])}"
            elif row["boost_used"] >= row["boost_max"]:
                next_boost = "лимит исчерпан"
            else:
                next_boost = "доступно сейчас"
        else:
            next_boost = "—"

        lines.extend(
            [
                f"\n{idx}) #{row['plant_id']} {row['tree_title']} · {row['rarity']}",
                f"🌰 Семя: {row['seed_title']}",
                f"📍 {state_line}",
                f"📊 {_progress_bar(row['progress'])}",
                f"⚡ Ускорения: {row['boost_used']}/{row['boost_max']} | Следующее: {next_boost}",
                f"💰 Примерная стоимость: ~{row['approx_value']}🪙",
            ]
        )
    return "\n".join(lines)


def inventory_card(state: UserState) -> str:
    seed_lines = [f"- {SEED_TYPES[s]['title']}: {q}" for s, q in state.seeds.items() if q > 0 and s in SEED_TYPES]
    crop_lines = [f"- {k}: {v}" for k, v in state.harvest.items() if v > 0]
    active_tool = TOOLS[state.active_tool]["title"] if state.active_tool in TOOLS else "нет"
    used_slots = sum(state.harvest.values())

    return (
        "🎒 Инвентарь\n"
        "────────────\n"
        f"📦 Предметы: {used_slots}/{state.inventory_capacity}"
        f" (следующие уровни: {', '.join(map(str, INVENTORY_CAPACITY_LEVELS))})\n"
        f"🛠 Активный инструмент: {active_tool}\n"
        f"📈 Уровень: {state.level} | XP: {state.xp}\n\n"
        + "🌱 Семена:\n"
        + ("\n".join(seed_lines) if seed_lines else "(пусто)")
        + "\n\n🧺 Дроп:\n"
        + ("\n".join(crop_lines) if crop_lines else "(пусто)")
    )


def tools_card(state: UserState) -> str:
    active_tool = TOOLS[state.active_tool]["title"] if state.active_tool in TOOLS else "нет"
    lines = ["🛠 Инструменты", "────────────", f"Активный: {active_tool}", ""]
    owned_lines = [
        f"• {TOOLS[tool_id]['title']} x{qty}"
        for tool_id, qty in state.owned_tools.items()
        if qty > 0 and tool_id in TOOLS
    ]
    lines.append("Коллекция:\n" + ("\n".join(owned_lines) if owned_lines else "(пусто)"))
    return "\n".join(lines)
