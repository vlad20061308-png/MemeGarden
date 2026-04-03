from __future__ import annotations

import random

from app.data.constants import (
    DEFAULT_INVENTORY_CAPACITY,
    INVENTORY_CAPACITY_LEVELS,
    MAX_FARM_SLOTS,
    SEED_TYPES,
    STATE_GROWING,
    STATE_READY,
    STATE_WILTED,
    TOOLS,
    TREE_TYPES,
)
from app.data.models import PlantRecord, UserState
from app.utils.storage import Storage
from app.utils.time_utils import now_ts


class GameService:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def user(self, user_id: int) -> UserState:
        return self.storage.get_or_create_user(user_id)

    def seed_catalog(self) -> dict:
        return SEED_TYPES

    def tool_catalog(self) -> dict:
        return TOOLS

    def inventory_used(self, user: UserState) -> int:
        return sum(user.harvest.values())

    def inventory_free(self, user: UserState) -> int:
        return max(user.inventory_capacity - self.inventory_used(user), 0)

    def _roll_weighted(self, weighted_map: dict[str, float]) -> str:
        roll = random.uniform(0, 100)
        cumulative = 0.0
        fallback = next(iter(weighted_map))
        for item_id, chance in weighted_map.items():
            if chance <= 0:
                continue
            cumulative += chance
            if roll <= cumulative:
                return item_id
            fallback = item_id
        return fallback

    def _plant_state(self, plant: PlantRecord) -> str:
        current = now_ts()
        if current < plant.due_at:
            return STATE_GROWING
        if current <= plant.wilt_at:
            return STATE_READY
        return STATE_WILTED

    def buy_seed(self, user_id: int, seed_id: str) -> tuple[bool, str]:
        if seed_id not in SEED_TYPES:
            return False, "Такого семени нет в магазине."
        user = self.user(user_id)
        data = SEED_TYPES[seed_id]
        if user.coins < data["price"]:
            return False, "Недостаточно монет."
        user.coins -= data["price"]
        user.seeds[seed_id] = user.seeds.get(seed_id, 0) + 1
        self.storage.save()
        return True, f"Куплено семя: {data['title']}"

    def buy_tool(self, user_id: int, tool_id: str) -> tuple[bool, str]:
        if tool_id not in TOOLS:
            return False, "Инструмент не найден."
        user = self.user(user_id)
        tool = TOOLS[tool_id]
        if user.coins < tool["price"]:
            return False, "Недостаточно монет."
        user.coins -= tool["price"]
        user.owned_tools[tool_id] = user.owned_tools.get(tool_id, 0) + 1
        if user.active_tool is None:
            user.active_tool = tool_id
        self.storage.save()
        return True, f"Куплен инструмент: {tool['title']}"

    def equip_tool(self, user_id: int, tool_id: str) -> tuple[bool, str]:
        user = self.user(user_id)
        if user.owned_tools.get(tool_id, 0) <= 0:
            return False, "Сначала купи этот инструмент."
        user.active_tool = tool_id
        self.storage.save()
        return True, f"Активный инструмент: {TOOLS[tool_id]['title']}"

    def plant_seed(self, user_id: int, seed_id: str) -> tuple[bool, str]:
        user = self.user(user_id)
        if len(user.farm) >= MAX_FARM_SLOTS:
            return False, "Ферма заполнена. Сначала собери или убери растения."
        if user.seeds.get(seed_id, 0) <= 0:
            return False, "Нет купленных семян этого типа."

        seed_data = SEED_TYPES[seed_id]
        tree_id = self._roll_weighted(seed_data["trees"])
        tree_data = TREE_TYPES[tree_id]

        tool_pct = 0
        if user.active_tool and user.active_tool in TOOLS:
            tool_pct = TOOLS[user.active_tool]["reduction_pct"]

        base = tree_data["grow_seconds"]
        grow_seconds = max(int(base * (100 - tool_pct) / 100), 60)
        ready_window = max(600, int(grow_seconds * 0.5))
        current = now_ts()

        user.seeds[seed_id] -= 1
        if user.seeds[seed_id] == 0:
            user.seeds.pop(seed_id, None)

        user.farm.append(
            PlantRecord(
                plant_id=user.next_plant_id,
                seed_id=seed_id,
                tree_id=tree_id,
                planted_at=current,
                due_at=current + grow_seconds,
                wilt_at=current + grow_seconds + ready_window,
                grow_seconds=grow_seconds,
                ready_window_seconds=ready_window,
            )
        )
        user.next_plant_id += 1
        self.storage.save()
        tool_note = f" (инструмент: -{tool_pct}%)" if tool_pct else ""
        return True, f"Посажено: {seed_data['title']} → {tree_data['title']}{tool_note}"

    def get_farm_view(self, user_id: int) -> list[dict]:
        user = self.user(user_id)
        current = now_ts()
        rows: list[dict] = []
        for plant in user.farm:
            tree = TREE_TYPES[plant.tree_id]
            boost = tree["boost"]
            state = self._plant_state(plant)
            remaining = int(max(plant.due_at - current, 0))
            next_boost_in = 0
            if state == STATE_GROWING and plant.boost_clicks_used < boost["max_clicks"]:
                next_allowed = plant.boost_last_at + boost["interval"] if plant.boost_last_at else 0
                next_boost_in = int(max(next_allowed - current, 0))

            progress = min(max((current - plant.planted_at) / max(plant.grow_seconds, 1), 0), 1)
            approx_value = int(sum(item["price"] * item["chance"] / 100 for item in tree["drops"]))

            rows.append(
                {
                    "plant_id": plant.plant_id,
                    "seed_id": plant.seed_id,
                    "seed_title": SEED_TYPES.get(plant.seed_id, {}).get("title", plant.seed_id),
                    "tree_id": plant.tree_id,
                    "tree_title": tree["title"],
                    "rarity": tree["rarity"],
                    "state": state,
                    "time_left": remaining,
                    "progress": progress,
                    "boost_used": plant.boost_clicks_used,
                    "boost_max": boost["max_clicks"],
                    "next_boost_in": next_boost_in,
                    "boost_interval": boost["interval"],
                    "approx_value": approx_value,
                }
            )
        return rows

    def boost_plant(self, user_id: int, plant_id: int) -> tuple[bool, str]:
        user = self.user(user_id)
        plant = next((p for p in user.farm if p.plant_id == plant_id), None)
        if not plant:
            return False, "Растение не найдено."

        state = self._plant_state(plant)
        if state != STATE_GROWING:
            return False, "Ускорять можно только пока растение растёт."

        boost_data = TREE_TYPES[plant.tree_id]["boost"]
        if plant.boost_clicks_used >= boost_data["max_clicks"]:
            return False, "Лимит ускорений для этого растения исчерпан."

        current = now_ts()
        if plant.boost_last_at and current < plant.boost_last_at + boost_data["interval"]:
            left = int((plant.boost_last_at + boost_data["interval"]) - current)
            return False, f"Следующее ускорение будет доступно через {left}с."

        plant.boost_clicks_used += 1
        plant.boost_last_at = current
        plant.due_at = max(current, plant.due_at - boost_data["reduce"])
        plant.wilt_at = plant.due_at + plant.ready_window_seconds
        self.storage.save()
        return True, "Ускорение применено."

    def _roll_drop(self, tree_id: str) -> dict:
        drops = TREE_TYPES[tree_id]["drops"]
        roll = random.uniform(0, 100)
        cumulative = 0.0
        fallback = drops[-1]
        for drop in drops:
            cumulative += drop["chance"]
            if roll <= cumulative:
                return drop
            fallback = drop
        return fallback

    def harvest(self, user_id: int) -> dict:
        user = self.user(user_id)
        harvested = 0
        coins = 0
        wilted_removed = 0
        blocked = 0
        drops: list[str] = []

        if user.inventory_capacity not in INVENTORY_CAPACITY_LEVELS:
            user.inventory_capacity = DEFAULT_INVENTORY_CAPACITY

        new_farm: list[PlantRecord] = []
        for plant in user.farm:
            state = self._plant_state(plant)
            if state == STATE_WILTED:
                wilted_removed += 1
                continue

            if state == STATE_READY:
                if self.inventory_free(user) <= 0:
                    blocked += 1
                    new_farm.append(plant)
                    continue
                drop = self._roll_drop(plant.tree_id)
                user.harvest[drop["id"]] = user.harvest.get(drop["id"], 0) + 1
                user.coins += drop["price"]
                harvested += 1
                coins += drop["price"]
                drops.append(drop["title"])
                continue

            new_farm.append(plant)

        user.farm = new_farm
        self.storage.save()
        return {
            "harvested": harvested,
            "coins": coins,
            "wilted": wilted_removed,
            "blocked": blocked,
            "drops": drops,
        }

    def drop_one_item(self, user_id: int, item_id: str) -> tuple[bool, str]:
        user = self.user(user_id)
        if user.harvest.get(item_id, 0) <= 0:
            return False, "Такого предмета нет в инвентаре."
        user.harvest[item_id] -= 1
        if user.harvest[item_id] == 0:
            user.harvest.pop(item_id, None)
        self.storage.save()
        return True, "1 предмет удалён из инвентаря."

    def force_ready_all(self, user_id: int) -> tuple[bool, str]:
        user = self.user(user_id)
        current = now_ts()
        changed = 0
        for plant in user.farm:
            if self._plant_state(plant) == STATE_GROWING:
                plant.due_at = current
                plant.wilt_at = current + plant.ready_window_seconds
                changed += 1
        self.storage.save()
        return True, f"Готово к сбору: {changed} растений."

    def force_ready_one(self, user_id: int, plant_id: int) -> tuple[bool, str]:
        user = self.user(user_id)
        plant = next((p for p in user.farm if p.plant_id == plant_id), None)
        if not plant:
            return False, f"Растение #{plant_id} не найдено."
        current = now_ts()
        plant.due_at = current
        plant.wilt_at = current + plant.ready_window_seconds
        self.storage.save()
        return True, f"Растение #{plant_id} переведено в ready."

    def force_wilt_all(self, user_id: int) -> tuple[bool, str]:
        user = self.user(user_id)
        current = now_ts()
        changed = 0
        for plant in user.farm:
            if self._plant_state(plant) != STATE_WILTED:
                plant.due_at = current - 1
                plant.wilt_at = current - 1
                changed += 1
        self.storage.save()
        return True, f"Засушено растений: {changed}."

    def set_balance(self, user_id: int, amount: int) -> tuple[bool, str]:
        if amount < 0:
            return False, "Баланс не может быть отрицательным."
        user = self.user(user_id)
        user.coins = amount
        self.storage.save()
        return True, f"Баланс установлен: {user.coins}🪙"

    def add_balance(self, user_id: int, amount: int) -> tuple[bool, str]:
        if amount < 0:
            return False, "Сумма должна быть неотрицательной."
        user = self.user(user_id)
        user.coins += amount
        self.storage.save()
        return True, f"Добавлено {amount}🪙. Баланс: {user.coins}🪙"

    def take_balance(self, user_id: int, amount: int) -> tuple[bool, str]:
        if amount < 0:
            return False, "Сумма должна быть неотрицательной."
        user = self.user(user_id)
        user.coins = max(user.coins - amount, 0)
        self.storage.save()
        return True, f"Списано {amount}🪙 (не ниже 0). Баланс: {user.coins}🪙"

    def get_dev_state(self, user_id: int, dev_mode: bool) -> dict:
        user = self.user(user_id)
        plants = [
            {
                "plant_id": plant.plant_id,
                "state": self._plant_state(plant),
                "due_at": int(plant.due_at),
                "wilt_at": int(plant.wilt_at),
            }
            for plant in user.farm
        ]
        return {
            "user_id": user_id,
            "dev_mode": dev_mode,
            "balance": user.coins,
            "active_tool": user.active_tool or "нет",
            "seeds_count": sum(user.seeds.values()),
            "plants_count": len(user.farm),
            "plants": plants,
        }
