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


def start_card(hub: dict) -> str:
    return (
        "🌿 MemeGarden\n"
        "Твоя уютная ферма мем-деревьев уже ждёт.\n\n"
        "🏡 Игровой хаб\n"
        f"💰 Баланс: {hub['coins']}🪙\n"
        f"📈 Уровень: {hub['level']} · XP: {hub['xp']}\n"
        f"🌱 Ферма: {hub['farm_total']}/{MAX_FARM_SLOTS} "
        f"(⏳ {hub['farm_growing']} · ✅ {hub['farm_ready']} · 🥀 {hub['farm_wilted']})\n"
        f"🎒 Рюкзак: {hub['inventory_used']}/{hub['inventory_capacity']}\n\n"
        "⬇️ Разделы — на нижней клавиатуре."
    )


def menu_hint_card(hub: dict) -> str:
    return (
        "🏠 Главное меню\n"
        f"💰 {hub['coins']}🪙 · 📈 lvl {hub['level']} · 🌾 ready: {hub['farm_ready']}\n"
        "Открой нужный раздел кнопками ниже или через inline-навигацию."
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
        "⚙️ Настройки и помощь\n"
        "Команды: /start /help /shop /plant /farm /harvest /inventory /balance /level\n\n"
        "Если интерфейс не обновился — нажми «🔄 Обновить» в ферме."
    )


def shop_card() -> str:
    lines = ["🏪 Рынок MemeGarden", "Подбери покупки под свой стиль игры.", "", "🌱 Семена"]
    for data in SEED_TYPES.values():
        lines.append(f"• {data['title']} — {data['price']}🪙")

    lines.extend(["", "🛠 Инструменты"])
    for data in TOOLS.values():
        lines.append(f"• {data['title']} — {data['price']}🪙 (−{data['reduction_pct']}% времени роста)")
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


def farm_card(farm_rows: list[dict], action_state: dict) -> str:
    lines = [
        f"🚜 Ферма {len(farm_rows)}/{MAX_FARM_SLOTS}",
        f"Статус: ⏳ {action_state['farm_counts']['growing']} · ✅ {action_state['farm_counts']['ready']} · 🥀 {action_state['farm_counts']['wilted']}",
        "────────────",
    ]
    if not farm_rows:
        lines.append("Пока пусто. Загляни в рынок, купи семена и начинай цикл роста.")

    for idx, row in enumerate(farm_rows, start=1):
        if row["state"] == STATE_GROWING:
            state_line = f"⏳ Растёт: {format_seconds(row['time_left'])}"
        elif row["state"] == STATE_READY:
            state_line = "✅ Готово к сбору"
        else:
            state_line = "🥀 Засохло (уберётся через сбор)"

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
                f"🌰 {row['seed_title']}",
                f"📍 {state_line}",
                f"📊 {_progress_bar(row['progress'])}",
                f"⚡ {row['boost_used']}/{row['boost_max']} · следующее: {next_boost}",
                f"💰 ~{row['approx_value']}🪙",
            ]
        )
    return "\n".join(lines)


def inventory_card(state: UserState) -> str:
    seed_lines = [f"• {SEED_TYPES[s]['title']}: {q}" for s, q in state.seeds.items() if q > 0 and s in SEED_TYPES]
    crop_lines = [f"• {k}: {v}" for k, v in state.harvest.items() if v > 0]
    active_tool = TOOLS[state.active_tool]["title"] if state.active_tool in TOOLS else "нет"
    used_slots = sum(state.harvest.values())

    return (
        "🎒 Рюкзак\n"
        "────────────\n"
        f"📦 Предметы: {used_slots}/{state.inventory_capacity}"
        f" (уровни: {', '.join(map(str, INVENTORY_CAPACITY_LEVELS))})\n"
        f"🛠 Активный инструмент: {active_tool}\n"
        f"📈 Уровень: {state.level} · XP: {state.xp}\n\n"
        + "🌱 Семена:\n"
        + ("\n".join(seed_lines) if seed_lines else "(пусто)")
        + "\n\n🌾 Дроп:\n"
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
