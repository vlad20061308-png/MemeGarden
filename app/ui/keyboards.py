from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.data.constants import SEED_TYPES, TOOLS
from app.data.models import UserState


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("🚜 Ферма"), KeyboardButton("🏪 Рынок")],
        [KeyboardButton("🎒 Рюкзак"), KeyboardButton("🧭 Экспедиция")],
        [KeyboardButton("👤 Профиль")],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


def main_menu_keyboard(can_expedition: bool = True) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("🚜 Ферма", callback_data="menu_open:farm"),
            InlineKeyboardButton("🏪 Рынок", callback_data="menu_open:shop"),
        ],
        [
            InlineKeyboardButton("🎒 Рюкзак", callback_data="menu_open:inventory"),
            InlineKeyboardButton("👤 Профиль", callback_data="menu_open:profile"),
        ],
        [
            InlineKeyboardButton(
                "🧭 В экспедицию" if can_expedition else "❌ В экспедицию",
                callback_data="menu_open:expedition" if can_expedition else "unavailable:expedition",
            )
        ],
        [InlineKeyboardButton("🔄 Обновить", callback_data="menu_open:refresh")],
    ]
    return InlineKeyboardMarkup(rows)


def shop_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("🌱 Семена", callback_data="shop_section:seeds"),
            InlineKeyboardButton("🛠 Инструменты", callback_data="shop_section:tools"),
        ],
        [
            InlineKeyboardButton("🚜 На ферму", callback_data="menu_open:farm"),
            InlineKeyboardButton("🏠 В меню", callback_data="menu_back"),
        ],
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
    rows.append([InlineKeyboardButton("⬅️ Разделы рынка", callback_data="menu_open:shop")])
    rows.append([InlineKeyboardButton("🏠 В меню", callback_data="menu_back")])
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
    rows.append([InlineKeyboardButton("⬅️ Разделы рынка", callback_data="menu_open:shop")])
    rows.append([InlineKeyboardButton("🏠 В меню", callback_data="menu_back")])
    return InlineKeyboardMarkup(rows)


def plant_keyboard(user_seeds: dict[str, int], can_plant: bool) -> InlineKeyboardMarkup:
    rows = []
    if can_plant:
        for seed_id, qty in user_seeds.items():
            if qty > 0 and seed_id in SEED_TYPES:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"🪴 {SEED_TYPES[seed_id]['title']} x{qty}",
                            callback_data=f"plant_seed:{seed_id}",
                        )
                    ]
                )

    if not rows:
        rows.append([InlineKeyboardButton("❌ Сейчас посадка недоступна", callback_data="unavailable:plant")])

    rows.append(
        [
            InlineKeyboardButton("🚜 К ферме", callback_data="menu_open:farm"),
            InlineKeyboardButton("🏠 В меню", callback_data="menu_back"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def farm_keyboard(action_state: dict, can_expedition: bool) -> InlineKeyboardMarkup:
    boost_callback = (
        f"farm_boost:{action_state['boost_plant_id']}" if action_state["can_accelerate"] else "unavailable:boost"
    )
    harvest_callback = "farm_harvest" if action_state["can_harvest"] else "unavailable:harvest"
    plant_callback = "menu_open:plant" if action_state["can_plant"] else "unavailable:plant"

    rows = [
        [
            InlineKeyboardButton(
                "⚡ Ускорить" if action_state["can_accelerate"] else "❌ Ускорить",
                callback_data=boost_callback,
            ),
            InlineKeyboardButton(
                "🌾 Собрать" if action_state["can_harvest"] else "❌ Собрать",
                callback_data=harvest_callback,
            ),
        ],
        [
            InlineKeyboardButton(
                "🪴 Посадить" if action_state["can_plant"] else "❌ Посадить",
                callback_data=plant_callback,
            )
        ],
        [
            InlineKeyboardButton("🧭 Экспедиция" if can_expedition else "❌ Экспедиция", callback_data="menu_open:expedition" if can_expedition else "unavailable:expedition"),
            InlineKeyboardButton("🔄 Обновить", callback_data="farm_refresh"),
        ],
        [
            InlineKeyboardButton("🏪 В рынок", callback_data="menu_open:shop"),
            InlineKeyboardButton("🏠 В меню", callback_data="menu_back"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def inventory_keyboard(state: UserState, has_seeds: bool, has_drops: bool, can_expedition: bool) -> InlineKeyboardMarkup:
    rows = []
    for tool_id, qty in state.owned_tools.items():
        if qty > 0 and tool_id in TOOLS:
            rows.append(
                [
                    InlineKeyboardButton(
                        f"🛠 Экипировать {TOOLS[tool_id]['title']}",
                        callback_data=f"equip_tool:{tool_id}",
                    )
                ]
            )

    for item_id, qty in state.harvest.items():
        if qty > 0:
            rows.append(
                [
                    InlineKeyboardButton(
                        f"🗑 Удалить {item_id} (-1)",
                        callback_data=f"drop_item:{item_id}",
                    )
                ]
            )

    rows.append(
        [
            InlineKeyboardButton("🪴 Посадить" if has_seeds else "❌ Посадить", callback_data="menu_open:plant" if has_seeds else "unavailable:plant"),
            InlineKeyboardButton("🌾 К сбору" if has_drops else "❌ Дроп пуст", callback_data="menu_open:farm" if has_drops else "unavailable:inventory"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton("🧭 Экспедиция" if can_expedition else "❌ Экспедиция", callback_data="menu_open:expedition" if can_expedition else "unavailable:expedition"),
            InlineKeyboardButton("🏠 В меню", callback_data="menu_back"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def expedition_keyboard(can_expedition: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                "🧭 В экспедицию" if can_expedition else "❌ В экспедицию",
                callback_data="expedition_run" if can_expedition else "unavailable:expedition",
            )
        ],
        [
            InlineKeyboardButton("🚜 На ферму", callback_data="menu_open:farm"),
            InlineKeyboardButton("🏠 В меню", callback_data="menu_back"),
        ],
    ]
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
