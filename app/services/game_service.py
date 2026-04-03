from __future__ import annotations

from app.data.constants import MAX_FARM_SLOTS, SHOP_ITEMS
from app.data.models import PlantRecord, UserState
from app.utils.storage import Storage
from app.utils.time_utils import now_ts


class GameService:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def user(self, user_id: int) -> UserState:
        return self.storage.get_or_create_user(user_id)

    def buy_seed(self, user_id: int, seed_id: str) -> tuple[bool, str]:
        if seed_id not in SHOP_ITEMS:
            return False, "Такого семени нет в магазине."
        user = self.user(user_id)
        item = SHOP_ITEMS[seed_id]
        if user.coins < item["price"]:
            return False, "Недостаточно монет."
        user.coins -= item["price"]
        user.seeds[seed_id] = user.seeds.get(seed_id, 0) + 1
        self.storage.save()
        return True, f"Куплено: {item['title']}"

    def plant_seed(self, user_id: int, seed_id: str) -> tuple[bool, str]:
        user = self.user(user_id)
        if len(user.farm) >= MAX_FARM_SLOTS:
            return False, "Ферма заполнена. Сначала собери урожай."
        if user.seeds.get(seed_id, 0) <= 0:
            return False, "Нет таких семян в инвентаре."
        item = SHOP_ITEMS[seed_id]
        user.seeds[seed_id] -= 1
        if user.seeds[seed_id] == 0:
            user.seeds.pop(seed_id, None)
        user.farm.append(
            PlantRecord(seed_id=seed_id, planted_at=now_ts(), grow_seconds=item["grow_seconds"])
        )
        self.storage.save()
        return True, f"Посажено: {item['title']}"

    def ready_to_harvest(self, user_id: int) -> list[PlantRecord]:
        user = self.user(user_id)
        now = now_ts()
        return [plant for plant in user.farm if now - plant.planted_at >= plant.grow_seconds]

    def harvest(self, user_id: int) -> tuple[int, int]:
        user = self.user(user_id)
        now = now_ts()
        ready = [plant for plant in user.farm if now - plant.planted_at >= plant.grow_seconds]
        if not ready:
            return 0, 0

        total_coins = 0
        for plant in ready:
            item = SHOP_ITEMS[plant.seed_id]
            crop_key = plant.seed_id.replace("_seed", "")
            user.harvest[crop_key] = user.harvest.get(crop_key, 0) + 1
            total_coins += item["sell_price"]

        user.farm = [plant for plant in user.farm if plant not in ready]
        user.coins += total_coins
        self.storage.save()
        return len(ready), total_coins
