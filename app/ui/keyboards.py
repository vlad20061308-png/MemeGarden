from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.data.constants import SHOP_ITEMS


def shop_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"Купить {data['title']} ({data['price']}🪙)", callback_data=f"shop_buy:{seed_id}"
            )
        ]
        for seed_id, data in SHOP_ITEMS.items()
    ]
    return InlineKeyboardMarkup(rows)


def plant_keyboard(user_seeds: dict[str, int]) -> InlineKeyboardMarkup:
    rows = []
    for seed_id, qty in user_seeds.items():
        if qty > 0 and seed_id in SHOP_ITEMS:
            rows.append(
                [
                    InlineKeyboardButton(
                        f"Посадить {SHOP_ITEMS[seed_id]['title']} x{qty}",
                        callback_data=f"plant_seed:{seed_id}",
                    )
                ]
            )
    if not rows:
        rows.append([InlineKeyboardButton("Нет доступных семян", callback_data="noop")])
    return InlineKeyboardMarkup(rows)


def farm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔄 Обновить ферму", callback_data="farm_refresh")]]
    )
