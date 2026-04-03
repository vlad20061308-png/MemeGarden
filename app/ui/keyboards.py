from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.data.constants import SEED_TYPES, TOOLS
from app.data.models import UserState


def main_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("🌱 Ферма", callback_data="menu_open:farm"),
            InlineKeyboardButton("🛒 Магазин", callback_data="menu_open:shop"),
        ],
        [
            InlineKeyboardButton("🎒 Инвентарь", callback_data="menu_open:inventory"),
            InlineKeyboardButton("🛠 Инструменты", callback_data="menu_open:tools"),
        ],
        [
            InlineKeyboardButton("🌰 Посадить", callback_data="menu_open:plant"),
            InlineKeyboardButton("🧺 Собрать", callback_data="menu_open:harvest"),
        ],
        [
            InlineKeyboardButton("👤 Профиль", callback_data="menu_open:profile"),
            InlineKeyboardButton("🔄 Обновить", callback_data="menu_open:refresh"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def shop_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("🌱 Семена", callback_data="shop_section:seeds"),
            InlineKeyboardButton("🛠 Инструменты", callback_data="shop_section:tools"),
        ],
        [InlineKeyboardButton("⬅️ В меню", callback_data="menu_back")],
    ]
    return InlineKeyboardMarkup(rows)


def shop_seeds_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for seed_id, data in SEED_TYPES.items():
        rows.append(
            [
                InlineKeyboardButton(
                    f"Купить {data['title']} ({data['price']}🪙)",
                    callback_data=f"shop_buy_seed:{seed_id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton("⬅️ Разделы магазина", callback_data="menu_open:shop")])
    rows.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_back")])
    return InlineKeyboardMarkup(rows)


def shop_tools_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for tool_id, data in TOOLS.items():
        rows.append(
            [
                InlineKeyboardButton(
                    f"Купить {data['title']} ({data['price']}🪙)",
                    callback_data=f"shop_buy_tool:{tool_id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton("⬅️ Разделы магазина", callback_data="menu_open:shop")])
    rows.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_back")])
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
    rows.append(
        [
            InlineKeyboardButton("🔄 Обновить ферму", callback_data="farm_refresh"),
            InlineKeyboardButton("🌰 Посадить", callback_data="menu_open:plant"),
        ]
    )
    rows.append([InlineKeyboardButton("⬅️ Главное меню", callback_data="menu_back")])
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
    rows.append(
        [
            InlineKeyboardButton("🛠 Инструменты", callback_data="menu_open:tools"),
            InlineKeyboardButton("⬅️ Главное меню", callback_data="menu_back"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def dev_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("⚡ Сделать всё готовым", callback_data="dev_ready_all")],
        [InlineKeyboardButton("🥀 Засушить всё", callback_data="dev_wilt_all")],
        [InlineKeyboardButton("💰 +1000", callback_data="dev_add_1000")],
        [InlineKeyboardButton("💰 Установить 100000", callback_data="dev_set_100000")],
        [InlineKeyboardButton("🔄 Обновить dev state", callback_data="dev_state_refresh")],
    ]
    return InlineKeyboardMarkup(rows)
