from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.data.constants import SEED_TYPES, TOOLS
from app.data.models import UserState


def shop_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton("🌱 Семена", callback_data="shop_section:seeds")]]
    for seed_id, data in SEED_TYPES.items():
        rows.append(
            [
                InlineKeyboardButton(
                    f"Купить {data['title']} ({data['price']}🪙)",
                    callback_data=f"shop_buy_seed:{seed_id}",
                )
            ]
        )

    rows.append([InlineKeyboardButton("🛠 Инструменты", callback_data="shop_section:tools")])
    for tool_id, data in TOOLS.items():
        rows.append(
            [
                InlineKeyboardButton(
                    f"Купить {data['title']} ({data['price']}🪙)",
                    callback_data=f"shop_buy_tool:{tool_id}",
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


def plant_keyboard(user_seeds: dict[str, int]) -> InlineKeyboardMarkup:
    rows = []
    for seed_id, qty in user_seeds.items():
        if qty > 0 and seed_id in SEED_TYPES:
            rows.append(
                [
                    InlineKeyboardButton(
                        f"Посадить {SEED_TYPES[seed_id]['title']} x{qty}",
                        callback_data=f"plant_seed:{seed_id}",
                    )
                ]
            )
    if not rows:
        rows.append([InlineKeyboardButton("Нет доступных семян", callback_data="noop")])
    return InlineKeyboardMarkup(rows)


def farm_keyboard(plant_ids: list[int]) -> InlineKeyboardMarkup:
    rows = []
    for pid in plant_ids[:4]:
        rows.append(
            [
                InlineKeyboardButton("⚡ Ускорить", callback_data=f"farm_boost:{pid}"),
                InlineKeyboardButton("🧺 Собрать", callback_data="farm_harvest"),
            ]
        )
    rows.append([InlineKeyboardButton("🔄 Обновить ферму", callback_data="farm_refresh")])
    rows.append([InlineKeyboardButton("⬅️ Меню", callback_data="menu_back")])
    return InlineKeyboardMarkup(rows)


def inventory_keyboard(state: UserState) -> InlineKeyboardMarkup:
    rows = []
    for tool_id, qty in state.owned_tools.items():
        if qty > 0 and tool_id in TOOLS:
            rows.append(
                [
                    InlineKeyboardButton(
                        f"Экипировать {TOOLS[tool_id]['title']}",
                        callback_data=f"equip_tool:{tool_id}",
                    )
                ]
            )

    for item_id, qty in state.harvest.items():
        if qty > 0:
            rows.append(
                [
                    InlineKeyboardButton(
                        f"Выбросить {item_id} (-1)",
                        callback_data=f"drop_item:{item_id}",
                    )
                ]
            )

    if not rows:
        rows.append([InlineKeyboardButton("Пока нечего нажимать", callback_data="noop")])
    rows.append([InlineKeyboardButton("⬅️ Меню", callback_data="menu_back")])
    return InlineKeyboardMarkup(rows)
