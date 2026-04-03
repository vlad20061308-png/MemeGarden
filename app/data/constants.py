from __future__ import annotations

DEFAULT_COINS = 100
MAX_FARM_SLOTS = 6

SHOP_ITEMS = {
    "wheat_seed": {
        "title": "🌾 Wheat Seed",
        "price": 10,
        "grow_seconds": 30,
        "sell_price": 20,
    },
    "carrot_seed": {
        "title": "🥕 Carrot Seed",
        "price": 20,
        "grow_seconds": 60,
        "sell_price": 38,
    },
    "apple_seed": {
        "title": "🍎 Apple Seed",
        "price": 35,
        "grow_seconds": 90,
        "sell_price": 65,
    },
}

COMMANDS = [
    ("start", "Запуск игры"),
    ("help", "Список команд"),
    ("shop", "Открыть магазин семян"),
    ("plant", "Посадить семена"),
    ("farm", "Проверить ферму"),
    ("harvest", "Собрать урожай"),
    ("inventory", "Показать инвентарь"),
    ("balance", "Баланс монет"),
]
