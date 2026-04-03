from __future__ import annotations

DEFAULT_COINS = 10
MAX_FARM_SLOTS = 6
DEFAULT_INVENTORY_CAPACITY = 6
INVENTORY_CAPACITY_LEVELS = [6, 12, 20, 35, 50]

STATE_GROWING = "growing"
STATE_READY = "ready"
STATE_WILTED = "wilted"

TREE_TYPES = {
    "apple": {
        "title": "🍎 Яблоня",
        "rarity": "Обычное",
        "chance": 60.0,
        "grow_seconds": 30 * 60,
        "boost": {"interval": 5 * 60, "reduce": 60, "max_clicks": 5},
        "drops": [
            {"id": "apple", "title": "🍎 Яблоко", "chance": 85.0, "price": 1},
            {"id": "gold", "title": "🥇 Золото", "chance": 10.0, "price": 10},
            {"id": "ruby", "title": "💎 Рубин", "chance": 5.0, "price": 25},
        ],
    },
    "birch": {
        "title": "🌳 Берёза",
        "rarity": "Необычное",
        "chance": 14.0,
        "grow_seconds": 2 * 60 * 60,
        "boost": {"interval": 20 * 60, "reduce": 5 * 60, "max_clicks": 5},
        "drops": [
            {"id": "sap", "title": "🧃 Сок", "chance": 85.0, "price": 5},
            {"id": "zebra", "title": "🦓 Зебра", "chance": 10.0, "price": 45},
            {"id": "inyan", "title": "☯️ Иньянь", "chance": 5.0, "price": 100},
        ],
    },
    "pine": {
        "title": "🌲 Сосна",
        "rarity": "Редкое",
        "chance": 8.0,
        "grow_seconds": 5 * 60 * 60,
        "boost": {"interval": 45 * 60, "reduce": 15 * 60, "max_clicks": 5},
        "drops": [
            {"id": "cones", "title": "🌰 Шишки", "chance": 85.0, "price": 10},
            {"id": "star", "title": "⭐ Звезда", "chance": 10.0, "price": 120},
            {"id": "gift", "title": "🎁 Подарок", "chance": 5.0, "price": 250},
        ],
    },
    "sakura": {
        "title": "🌸 Сакура",
        "rarity": "Эпическое",
        "chance": 4.0,
        "grow_seconds": 6 * 60 * 60,
        "boost": {"interval": 60 * 60, "reduce": 20 * 60, "max_clicks": 5},
        "drops": [
            {"id": "petal", "title": "🌺 Лепесток", "chance": 85.0, "price": 30},
            {"id": "branch", "title": "🪵 Ветка", "chance": 10.0, "price": 300},
            {"id": "cat", "title": "🐱 Кот", "chance": 5.0, "price": 750},
        ],
    },
    "palm": {
        "title": "🌴 Пальма",
        "rarity": "Легендарное",
        "chance": 2.0,
        "grow_seconds": 8 * 60 * 60,
        "boost": {"interval": 90 * 60, "reduce": 30 * 60, "max_clicks": 5},
        "drops": [
            {"id": "banana", "title": "🍌 Банан", "chance": 85.0, "price": 30},
            {"id": "coconut", "title": "🥥 Кокос", "chance": 10.0, "price": 600},
            {"id": "ball", "title": "⚽ Мяч", "chance": 5.0, "price": 1500},
        ],
    },
    "baobab": {
        "title": "🪴 Баобаб",
        "rarity": "Мифическое",
        "chance": 0.75,
        "grow_seconds": 12 * 60 * 60,
        "boost": {"interval": 2 * 60 * 60, "reduce": 45 * 60, "max_clicks": 6},
        "drops": [
            {"id": "beans", "title": "🫘 Зерна", "chance": 85.0, "price": 200},
            {"id": "choco", "title": "🍫 Шоколад", "chance": 10.0, "price": 2000},
            {"id": "hare", "title": "🐇 Заяц", "chance": 5.0, "price": 5000},
        ],
    },
    "secret": {
        "title": "🕵️ Тайное дерево",
        "rarity": "Секретное",
        "chance": 0.2,
        "grow_seconds": 15 * 60 * 60,
        "boost": {"interval": 2 * 60 * 60, "reduce": 45 * 60, "max_clicks": 6},
        "drops": [
            {"id": "secret_drop", "title": "🧿 Специальный дроп", "chance": 100.0, "price": 1000},
        ],
    },
    "zolo": {
        "title": "🌟 Золо",
        "rarity": "Уникальное",
        "chance": 0.05,
        "grow_seconds": 24 * 60 * 60,
        "boost": {"interval": 3 * 60 * 60, "reduce": 60 * 60, "max_clicks": 6},
        "drops": [
            {"id": "unique_drop", "title": "👑 Уникальный дроп", "chance": 100.0, "price": 4000},
        ],
    },
}

SEED_TYPES = {
    "starter_seed": {
        "title": "🌱 Стартовое",
        "price": 5,
        "trees": {"apple": 98.0, "birch": 1.99, "zolo": 0.01, "secret": 0.0},
    },
    "common_seed": {
        "title": "🌾 Обычное",
        "price": 25,
        "trees": {"apple": 80.0, "birch": 19.0, "pine": 0.9, "zolo": 0.08, "secret": 0.02},
    },
    "uncommon_seed": {
        "title": "🍀 Необычное",
        "price": 100,
        "trees": {"birch": 60.0, "pine": 35.0, "sakura": 4.8, "zolo": 0.15, "secret": 0.05},
    },
    "rare_seed": {
        "title": "💠 Редкое",
        "price": 400,
        "trees": {"pine": 50.0, "sakura": 40.0, "palm": 9.7, "zolo": 0.25, "secret": 0.05},
    },
    "epic_seed": {
        "title": "🔥 Эпическое",
        "price": 1500,
        "trees": {"sakura": 60.0, "palm": 30.0, "baobab": 9.0, "zolo": 0.8, "secret": 0.2},
    },
    "mythic_seed": {
        "title": "🌀 Мифическое",
        "price": 5000,
        "trees": {"palm": 60.0, "baobab": 38.5, "zolo": 1.1, "secret": 0.4},
    },
    "divine_seed": {
        "title": "✨ Божественное",
        "price": 15000,
        "trees": {"baobab": 97.0, "zolo": 2.0, "secret": 1.0},
    },
}

TOOLS = {
    "plastic": {"title": "🪣 Пластиковая", "price": 150, "reduction_pct": 10},
    "steel": {"title": "⚙️ Стальная", "price": 600, "reduction_pct": 25},
    "gold": {"title": "🥇 Золотая", "price": 2500, "reduction_pct": 50},
    "diamond": {"title": "💎 Алмазная", "price": 7500, "reduction_pct": 80},
}



LEVEL_XP_REQUIREMENTS = {level: level * 100 for level in range(1, 36)}
MAX_LEVEL = max(LEVEL_XP_REQUIREMENTS)

XP_REWARDS = {
    "plant_seed": 8,
    "harvest_base": 18,
    "harvest_rarity_bonus": {
        "Обычное": 0,
        "Необычное": 4,
        "Редкое": 8,
        "Эпическое": 14,
        "Легендарное": 20,
        "Мифическое": 28,
        "Секретное": 36,
        "Уникальное": 45,
    },
    "rare_drop_bonus": 12,
    "epic_drop_bonus": 24,
    "rare_drop_threshold": 10.0,
    "epic_drop_threshold": 5.0,
}

LEVEL_REWARDS = {
    1: {"coins": 25, "seeds": {"starter_seed": 2}},
    2: {"coins": 35},
    3: {"coins": 45, "seeds": {"starter_seed": 1}},
    4: {"coins": 60},
    5: {"coins": 90, "seeds": {"common_seed": 1}},
    6: {"coins": 120},
    7: {"coins": 150, "seeds": {"common_seed": 1}},
    8: {"coins": 180, "inventory_capacity_bonus": 2},
    9: {"coins": 220},
    10: {"coins": 260, "tools": {"plastic": 1}, "seeds": {"uncommon_seed": 1}},
    11: {"coins": 320},
    12: {"coins": 380, "seeds": {"uncommon_seed": 1}},
    13: {"coins": 450},
    14: {"coins": 530},
    15: {"coins": 620, "seeds": {"rare_seed": 1}},
    16: {"coins": 720, "inventory_capacity_bonus": 2},
    17: {"coins": 840},
    18: {"coins": 980, "seeds": {"rare_seed": 1}},
    19: {"coins": 1140},
    20: {"coins": 1320, "tools": {"steel": 1}},
    21: {"coins": 1520},
    22: {"coins": 1740, "seeds": {"epic_seed": 1}},
    23: {"coins": 1980},
    24: {"coins": 2250, "inventory_capacity_bonus": 3},
    25: {"coins": 2550, "seeds": {"epic_seed": 1}},
    26: {"coins": 2880},
    27: {"coins": 3240, "seeds": {"mythic_seed": 1}},
    28: {"coins": 3630},
    29: {"coins": 4050},
    30: {"coins": 4510, "tools": {"gold": 1}, "seeds": {"mythic_seed": 1}},
    31: {"coins": 5010},
    32: {"coins": 5550, "inventory_capacity_bonus": 3},
    33: {"coins": 6130, "seeds": {"divine_seed": 1}},
    34: {"coins": 6760},
    35: {"coins": 7440, "tools": {"diamond": 1}, "seeds": {"divine_seed": 1}},
}

COMMANDS = [
    ("start", "Запуск игры"),
    ("help", "Список команд"),
    ("shop", "Магазин семян и инструментов"),
    ("plant", "Посадить купленное семя"),
    ("farm", "Проверить ферму"),
    ("harvest", "Собрать готовый урожай"),
    ("inventory", "Инвентарь и инструмент"),
    ("balance", "Баланс монет"),
    ("level", "Уровень и XP"),
]
