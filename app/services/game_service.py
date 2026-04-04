from __future__ import annotations

import random

from app.data.constants import (
    DEFAULT_INVENTORY_CAPACITY,
    INVENTORY_CAPACITY_LEVELS,
    LEVEL_REWARDS,
    LEVEL_XP_REQUIREMENTS,
    MAX_FARM_SLOTS,
    MAX_LEVEL,
    SEED_TYPES,
    STATE_GROWING,
    STATE_READY,
    STATE_WILTED,
    TOOLS,
    TREE_TYPES,
    XP_REWARDS,
)
from app.data.models import PlantRecord, UserState
from app.utils.storage import Storage
from app.utils.time_utils import now_ts


class GameService:
    META_XP_KEY = "__meta_xp"
    META_LEVEL_KEY = "__meta_level"
    META_CLAIM_MASK_KEY = "__meta_level_claim_mask"

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def _claimed_levels_to_mask(self, levels: list[int]) -> int:
        mask = 0
        for level in levels:
            if 1 <= level <= 63:
                mask |= 1 << level
        return mask

    def _claimed_levels_from_mask(self, mask: int) -> list[int]:
        levels: list[int] = []
        for level in range(1, MAX_LEVEL + 1):
            if mask & (1 << level):
                levels.append(level)
        return levels

    def _load_progression_meta(self, user: UserState) -> bool:
        changed = False

        xp_meta = user.owned_tools.get(self.META_XP_KEY)
        if xp_meta is not None and user.xp == 0:
            user.xp = max(int(xp_meta), 0)
            changed = True

        level_meta = user.owned_tools.get(self.META_LEVEL_KEY)
        if level_meta is not None and user.level == 0:
            user.level = max(int(level_meta), 0)
            changed = True

        claim_mask = user.owned_tools.get(self.META_CLAIM_MASK_KEY)
        if claim_mask is not None and not user.claimed_level_rewards:
            user.claimed_level_rewards = self._claimed_levels_from_mask(max(int(claim_mask), 0))
            changed = True

        calculated_level = self.get_level_from_xp(user.xp)
        if user.level != calculated_level:
            user.level = calculated_level
            changed = True

        user.claimed_level_rewards = sorted({level for level in user.claimed_level_rewards if level > 0})
        return changed

    def _store_progression_meta(self, user: UserState) -> None:
        user.owned_tools[self.META_XP_KEY] = max(user.xp, 0)
        user.owned_tools[self.META_LEVEL_KEY] = max(user.level, 0)
        user.owned_tools[self.META_CLAIM_MASK_KEY] = self._claimed_levels_to_mask(
            user.claimed_level_rewards
        )

    def _save_user(self, user: UserState) -> None:
        self._store_progression_meta(user)
        self.storage.save()

    def user(self, user_id: int) -> UserState:
        user = self.storage.get_or_create_user(user_id)
        if self._load_progression_meta(user):
            self._save_user(user)
        return user

    def seed_catalog(self) -> dict:
        return SEED_TYPES

    def tool_catalog(self) -> dict:
        return TOOLS

    def inventory_used(self, user: UserState) -> int:
        return sum(user.harvest.values())

    def inventory_free(self, user: UserState) -> int:
        return max(user.inventory_capacity - self.inventory_used(user), 0)

    def get_level_from_xp(self, xp: int) -> int:
        current_level = 0
        for level, required_xp in LEVEL_XP_REQUIREMENTS.items():
            if xp >= required_xp:
                current_level = level
            else:
                break
        return current_level

    def _collect_new_levels(self, old_level: int, new_level: int) -> list[int]:
        if new_level <= old_level:
            return []
        return list(range(old_level + 1, new_level + 1))

    def _apply_level_rewards(self, user_state: UserState, unlocked_levels: list[int]) -> list[dict]:
        granted_rewards: list[dict] = []
        claimed = set(user_state.claimed_level_rewards)

        for level in unlocked_levels:
            if level in claimed:
                continue

            reward_cfg = LEVEL_REWARDS.get(level, {})
            reward_result = {
                "level": level,
                "coins": 0,
                "seeds": {},
                "tools": {},
                "inventory_capacity_bonus": 0,
            }

            coins = int(reward_cfg.get("coins", 0))
            if coins > 0:
                user_state.coins += coins
                reward_result["coins"] = coins

            for seed_id, amount in reward_cfg.get("seeds", {}).items():
                amount_int = int(amount)
                if amount_int <= 0:
                    continue
                user_state.seeds[seed_id] = user_state.seeds.get(seed_id, 0) + amount_int
                reward_result["seeds"][seed_id] = amount_int

            for tool_id, amount in reward_cfg.get("tools", {}).items():
                amount_int = int(amount)
                if amount_int <= 0:
                    continue
                user_state.owned_tools[tool_id] = user_state.owned_tools.get(tool_id, 0) + amount_int
                reward_result["tools"][tool_id] = amount_int
                if user_state.active_tool is None and tool_id in TOOLS:
                    user_state.active_tool = tool_id

            inv_bonus = int(reward_cfg.get("inventory_capacity_bonus", 0))
            if inv_bonus > 0:
                user_state.inventory_capacity += inv_bonus
                reward_result["inventory_capacity_bonus"] = inv_bonus

            claimed.add(level)
            user_state.claimed_level_rewards.append(level)
            granted_rewards.append(reward_result)

        user_state.claimed_level_rewards = sorted(set(user_state.claimed_level_rewards))
        return granted_rewards

    def _add_xp_to_user(self, user: UserState, amount: int, reason: str | None, save: bool) -> dict:
        xp_added = max(int(amount), 0)
        old_level = user.level

        if xp_added > 0:
            user.xp += xp_added

        new_level = self.get_level_from_xp(user.xp)
        user.level = new_level

        unlocked_levels = self._collect_new_levels(old_level, new_level)
        granted_rewards = self._apply_level_rewards(user, unlocked_levels)

        if save and (xp_added > 0 or granted_rewards):
            self._save_user(user)

        return {
            "reason": reason,
            "xp_added": xp_added,
            "xp_total": user.xp,
            "old_level": old_level,
            "new_level": new_level,
            "leveled_up": new_level > old_level,
            "unlocked_levels": unlocked_levels,
            "granted_rewards": granted_rewards,
        }

    def add_xp(self, user_id: int, amount: int, reason: str | None = None) -> dict:
        user = self.user(user_id)
        return self._add_xp_to_user(user, amount, reason=reason, save=True)

    def get_level_progress(self, user_id: int) -> dict:
        user = self.user(user_id)
        next_level = user.level + 1 if user.level < MAX_LEVEL else None
        next_level_xp = LEVEL_XP_REQUIREMENTS.get(next_level) if next_level else None
        current_level_xp = LEVEL_XP_REQUIREMENTS.get(user.level, 0)
        xp_to_next = max((next_level_xp - user.xp), 0) if next_level_xp else 0
        return {
            "level": user.level,
            "xp": user.xp,
            "next_level": next_level,
            "next_level_xp": next_level_xp,
            "current_level_xp": current_level_xp,
            "xp_to_next": xp_to_next,
        }

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
        self._save_user(user)
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
        self._save_user(user)
        return True, f"Куплен инструмент: {tool['title']}"

    def equip_tool(self, user_id: int, tool_id: str) -> tuple[bool, str]:
        user = self.user(user_id)
        if user.owned_tools.get(tool_id, 0) <= 0:
            return False, "Сначала купи этот инструмент."
        user.active_tool = tool_id
        self._save_user(user)
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

        xp_result = self._add_xp_to_user(
            user,
            XP_REWARDS["plant_seed"],
            reason="plant_seed",
            save=False,
        )
        self._save_user(user)

        tool_note = f" (инструмент: -{tool_pct}%)" if tool_pct else ""
        xp_note = f"\n✨ XP: +{xp_result['xp_added']} ({xp_result['xp_total']} всего)"
        level_note = ""
        if xp_result["leveled_up"]:
            level_note = f"\n🎉 Уровень повышен: {xp_result['old_level']} → {xp_result['new_level']}"
        return True, f"Посажено: {seed_data['title']} → {tree_data['title']}{tool_note}{xp_note}{level_note}"

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


    def get_farm_action_state(self, user_id: int) -> dict:
        user = self.user(user_id)
        farm_rows = self.get_farm_view(user_id)

        can_harvest = any(row["state"] in {STATE_READY, STATE_WILTED} for row in farm_rows)
        can_plant = len(user.farm) < MAX_FARM_SLOTS and sum(user.seeds.values()) > 0

        boost_plant_id = None
        for row in farm_rows:
            if row["state"] == STATE_GROWING and row["boost_used"] < row["boost_max"] and row["next_boost_in"] <= 0:
                boost_plant_id = row["plant_id"]
                break

        counts = {
            "growing": sum(1 for row in farm_rows if row["state"] == STATE_GROWING),
            "ready": sum(1 for row in farm_rows if row["state"] == STATE_READY),
            "wilted": sum(1 for row in farm_rows if row["state"] == STATE_WILTED),
        }

        return {
            "farm_rows": farm_rows,
            "can_harvest": can_harvest,
            "can_plant": can_plant,
            "can_accelerate": boost_plant_id is not None,
            "boost_plant_id": boost_plant_id,
            "has_seeds": sum(user.seeds.values()) > 0,
            "has_tools": any(qty > 0 and tool_id in TOOLS for tool_id, qty in user.owned_tools.items()),
            "has_inventory_items": self.inventory_used(user) > 0,
            "farm_counts": counts,
            "free_slots": max(MAX_FARM_SLOTS - len(user.farm), 0),
        }

    def get_hub_state(self, user_id: int) -> dict:
        user = self.user(user_id)
        farm_state = self.get_farm_action_state(user_id)
        return {
            "coins": user.coins,
            "level": user.level,
            "xp": user.xp,
            "farm_total": len(user.farm),
            "farm_ready": farm_state["farm_counts"]["ready"],
            "farm_growing": farm_state["farm_counts"]["growing"],
            "farm_wilted": farm_state["farm_counts"]["wilted"],
            "seeds_total": sum(user.seeds.values()),
            "inventory_used": self.inventory_used(user),
            "inventory_capacity": user.inventory_capacity,
        }
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
        self._save_user(user)
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

    def _xp_for_harvest(self, tree_id: str, drop: dict) -> int:
        rarity = TREE_TYPES[tree_id]["rarity"]
        total = XP_REWARDS["harvest_base"] + XP_REWARDS["harvest_rarity_bonus"].get(rarity, 0)
        drop_chance = float(drop.get("chance", 100.0))
        if drop_chance <= XP_REWARDS["epic_drop_threshold"]:
            total += XP_REWARDS["epic_drop_bonus"]
        elif drop_chance <= XP_REWARDS["rare_drop_threshold"]:
            total += XP_REWARDS["rare_drop_bonus"]
        return total

    def harvest(self, user_id: int) -> dict:
        user = self.user(user_id)
        harvested = 0
        coins = 0
        wilted_removed = 0
        blocked = 0
        drops: list[str] = []
        gained_xp = 0

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
                gained_xp += self._xp_for_harvest(plant.tree_id, drop)
                continue

            new_farm.append(plant)

        user.farm = new_farm
        xp_result = self._add_xp_to_user(user, gained_xp, reason="harvest", save=False)
        self._save_user(user)
        return {
            "harvested": harvested,
            "coins": coins,
            "wilted": wilted_removed,
            "blocked": blocked,
            "drops": drops,
            "xp": xp_result,
        }

    def drop_one_item(self, user_id: int, item_id: str) -> tuple[bool, str]:
        user = self.user(user_id)
        if user.harvest.get(item_id, 0) <= 0:
            return False, "Такого предмета нет в инвентаре."
        user.harvest[item_id] -= 1
        if user.harvest[item_id] == 0:
            user.harvest.pop(item_id, None)
        self._save_user(user)
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
        self._save_user(user)
        return True, f"Готово к сбору: {changed} растений."

    def force_ready_one(self, user_id: int, plant_id: int) -> tuple[bool, str]:
        user = self.user(user_id)
        plant = next((p for p in user.farm if p.plant_id == plant_id), None)
        if not plant:
            return False, f"Растение #{plant_id} не найдено."
        current = now_ts()
        plant.due_at = current
        plant.wilt_at = current + plant.ready_window_seconds
        self._save_user(user)
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
        self._save_user(user)
        return True, f"Засушено растений: {changed}."

    def set_balance(self, user_id: int, amount: int) -> tuple[bool, str]:
        if amount < 0:
            return False, "Баланс не может быть отрицательным."
        user = self.user(user_id)
        user.coins = amount
        self._save_user(user)
        return True, f"Баланс установлен: {user.coins}🪙"

    def add_balance(self, user_id: int, amount: int) -> tuple[bool, str]:
        if amount < 0:
            return False, "Сумма должна быть неотрицательной."
        user = self.user(user_id)
        user.coins += amount
        self._save_user(user)
        return True, f"Добавлено {amount}🪙. Баланс: {user.coins}🪙"

    def take_balance(self, user_id: int, amount: int) -> tuple[bool, str]:
        if amount < 0:
            return False, "Сумма должна быть неотрицательной."
        user = self.user(user_id)
        user.coins = max(user.coins - amount, 0)
        self._save_user(user)
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
            "level": user.level,
            "xp": user.xp,
        }
