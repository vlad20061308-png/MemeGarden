from __future__ import annotations

from app.data.constants import (
    INVENTORY_CAPACITY_LEVELS,
    MAX_FARM_SLOTS,
    SEED_TYPES,
    STATE_GROWING,
    STATE_READY,
    STATE_WILTED,
    TOOLS,
)
from app.data.models import UserState
from app.utils.time_utils import format_seconds


def help_card() -> str:
    return (
        "Команды:\n"
        "/start, /help, /shop, /plant, /farm, /harvest, /inventory, /balance"
    )


def shop_card() -> str:
    lines = ["🛒 Магазин MemeGarden", "", "🌱 Семена:"]
    for data in SEED_TYPES.values():
        lines.append(f"- {data['title']}: {data['price']}🪙")

    lines.extend(["", "🛠 Инструменты (снижают время роста при посадке):"])
    for data in TOOLS.values():
        lines.append(f"- {data['title']}: {data['price']}🪙 (−{data['reduction_pct']}%)")
    return "\n".join(lines)


def _progress_bar(progress: float, width: int = 10) -> str:
    filled = int(progress * width)
    return "🟩" * filled + "⬜" * (width - filled)


def farm_card(farm_rows: list[dict]) -> str:
    lines = [f"🌱 Ферма: {len(farm_rows)}/{MAX_FARM_SLOTS}"]
    if not farm_rows:
        lines.append("Пусто. Используй /plant.")

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
                f"\n{idx}) #{row['plant_id']} {row['tree_title']} ({row['rarity']})",
                f"Семя: {row['seed_title']}",
                state_line,
                f"Прогресс: {_progress_bar(row['progress'])}",
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
        f"Предметы: {used_slots}/{state.inventory_capacity}"
        f" (следующие уровни: {', '.join(map(str, INVENTORY_CAPACITY_LEVELS))})\n"
        f"Активный инструмент: {active_tool}\n\n"
        + "Семена:\n"
        + ("\n".join(seed_lines) if seed_lines else "(пусто)")
        + "\n\nДроп:\n"
        + ("\n".join(crop_lines) if crop_lines else "(пусто)")
    )
