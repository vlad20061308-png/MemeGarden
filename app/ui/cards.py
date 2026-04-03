from __future__ import annotations

from app.data.constants import MAX_FARM_SLOTS, SHOP_ITEMS
from app.data.models import UserState
from app.utils.time_utils import format_seconds, now_ts


def help_card() -> str:
    return (
        "Команды:\n"
        "/start, /help, /shop, /plant, /farm, /harvest, /inventory, /balance"
    )


def shop_card() -> str:
    lines = ["🛒 Магазин:"]
    for item in SHOP_ITEMS.values():
        lines.append(
            f"- {item['title']}: {item['price']}🪙, рост {item['grow_seconds']}с, продажа {item['sell_price']}🪙"
        )
    return "\n".join(lines)


def farm_card(state: UserState) -> str:
    lines = [f"🌱 Ферма: {len(state.farm)}/{MAX_FARM_SLOTS}"]
    current = now_ts()
    if not state.farm:
        lines.append("Пусто. Используй /plant.")
    for i, plant in enumerate(state.farm, start=1):
        item = SHOP_ITEMS[plant.seed_id]
        left = int(plant.grow_seconds - (current - plant.planted_at))
        status = "✅ готово" if left <= 0 else f"⏳ {format_seconds(left)}"
        lines.append(f"{i}. {item['title']} — {status}")
    return "\n".join(lines)


def inventory_card(state: UserState) -> str:
    seed_lines = [f"- {SHOP_ITEMS[s]['title']}: {q}" for s, q in state.seeds.items() if q > 0]
    crop_lines = [f"- {k}: {v}" for k, v in state.harvest.items() if v > 0]
    return (
        "🎒 Инвентарь\n"
        + "Семена:\n"
        + ("\n".join(seed_lines) if seed_lines else "(пусто)")
        + "\n\nУрожай:\n"
        + ("\n".join(crop_lines) if crop_lines else "(пусто)")
    )
