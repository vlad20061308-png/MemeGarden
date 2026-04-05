from __future__ import annotations

import random
from typing import Any

from app.data.constants import (
    DEFAULT_INVENTORY_CAPACITY,
    EVENT_COOLDOWN_RANGE_SECONDS,
    EVENT_DEFINITIONS,
    EVENT_DURATION_RANGE_SECONDS,
    EVENT_MINI_CHANCE,
    EVENT_MINI_DEFINITION,
    EVENT_MINI_DURATION_RANGE_SECONDS,
    EXPEDITION_DEFAULT_ENERGY,
    EXPEDITION_DEFAULT_MAX_ENERGY,
    EXPEDITION_ENERGY_COST,
    EXPEDITION_ENERGY_REGEN_SECONDS,
    EXPEDITION_LOOT_TABLE,
    INVENTORY_CAPACITY_LEVELS,
    ITEM_TITLES,
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
    META_ENERGY_KEY = "__meta_energy"
    META_MAX_ENERGY_KEY = "__meta_max_energy"
    META_ENERGY_REGEN_TS_KEY = "__meta_energy_regen_at"
    META_EVENT_KEY = "__global_event"
    META_EVENT_NEXT_TS_KEY = "__global_event_next_at"

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _safe_event(self, payload: object) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        event_id = str(payload.get("id", "")).strip()
        title = str(payload.get("title", "")).strip()
        if not event_id or not title:
            return None

        start_ts = max(self._safe_float(payload.get("start_ts"), 0.0), 0.0)
        end_ts = max(self._safe_float(payload.get("end_ts"), 0.0), 0.0)
        duration = max(int(self._safe_float(payload.get("duration"), 0)), 0)
        if end_ts <= start_ts:
            return None

        tree_bonus_raw = payload.get("tree_bonus", {})
        tree_bonus: dict[str, float] = {}
        if isinstance(tree_bonus_raw, dict):
            for tree_id, value in tree_bonus_raw.items():
                multiplier = self._safe_float(value, 1.0)
                if multiplier > 0:
                    tree_bonus[str(tree_id)] = multiplier

        growth_bonus = max(self._safe_float(payload.get("growth_bonus"), 0.0), 0.0)
        drop_bonus = max(self._safe_float(payload.get("drop_bonus"), 0.0), 0.0)
        extra_drop = None
        extra_raw = payload.get("extra_drop")
        if isinstance(extra_raw, dict):
            extra_id = str(extra_raw.get("id", "")).strip()
            extra_title = str(extra_raw.get("title", "")).strip()
            extra_chance = max(self._safe_float(extra_raw.get("chance"), 0.0), 0.0)
            if extra_id and extra_title and extra_chance > 0:
                extra_drop = {"id": extra_id, "title": extra_title, "chance": extra_chance}

        return {
            "id": event_id,
            "title": title,
            "duration": duration,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "tree_bonus": tree_bonus,
            "growth_bonus": growth_bonus,
            "drop_bonus": drop_bonus,
            "extra_drop": extra_drop,
        }

    def generate_random_event(self) -> dict[str, Any]:
        source_pool = EVENT_DEFINITIONS
        duration_range = EVENT_DURATION_RANGE_SECONDS
        if random.random() <= EVENT_MINI_CHANCE:
            source_pool = [EVENT_MINI_DEFINITION]
            duration_range = EVENT_MINI_DURATION_RANGE_SECONDS

        template = random.choice(source_pool)
        event = self._safe_event(template) or {
            "id": "fallback_event",
            "title": "✨ Lucky Hour",
            "tree_bonus": {},
            "growth_bonus": 0.0,
            "drop_bonus": 0.0,
            "extra_drop": None,
            "duration": 0,
            "start_ts": 0.0,
            "end_ts": 0.0,
        }

        current = now_ts()
        duration = random.randint(duration_range[0], duration_range[1])
        event["duration"] = duration
        event["start_ts"] = current
        event["end_ts"] = current + duration
        return event

    def get_current_event(self) -> dict[str, Any] | None:
        event = self._safe_event(self.storage.get_meta(self.META_EVENT_KEY))
        if not event:
            return None
        if now_ts() >= float(event.get("end_ts", 0.0)):
            return None
        return event

    def update_event_if_needed(self) -> dict[str, Any] | None:
        current_event = self.get_current_event()
        if current_event:
            return current_event

        current = now_ts()
        next_event_at = max(self._safe_float(self.storage.get_meta(self.META_EVENT_NEXT_TS_KEY), 0.0), 0.0)
        if current < next_event_at:
            self.storage.set_meta(self.META_EVENT_KEY, None)
            self.storage.save()
            return None

        new_event = self.generate_random_event()
        self.storage.set_meta(self.META_EVENT_KEY, new_event)
        cooldown = random.randint(EVENT_COOLDOWN_RANGE_SECONDS[0], EVENT_COOLDOWN_RANGE_SECONDS[1])
        self.storage.set_meta(self.META_EVENT_NEXT_TS_KEY, float(new_event["end_ts"]) + cooldown)
        self.storage.save()
        return new_event

    def _event_compact_view(self, event: dict[str, Any] | None) -> dict[str, Any]:
        if not event:
            return {"active": False}
        remaining = max(int(float(event.get("end_ts", 0.0)) - now_ts()), 0)
        return {
            "active": remaining > 0,
            "id": event.get("id", ""),
            "title": event.get("title", "Unknown Event"),
            "remaining_seconds": remaining,
            "growth_bonus": max(self._safe_float(event.get("growth_bonus"), 0.0), 0.0),
            "drop_bonus": max(self._safe_float(event.get("drop_bonus"), 0.0), 0.0),
            "extra_drop": event.get("extra_drop"),
        }

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

    def _load_energy_meta(self, user: UserState) -> bool:
        changed = False

        energy_meta = user.owned_tools.get(self.META_ENERGY_KEY)
        if energy_meta is not None:
            value = max(int(energy_meta), 0)
            if user.energy != value:
                user.energy = value
                changed = True

        max_energy_meta = user.owned_tools.get(self.META_MAX_ENERGY_KEY)
        if max_energy_meta is not None:
            max_value = max(int(max_energy_meta), 1)
            if user.max_energy != max_value:
                user.max_energy = max_value
                changed = True

        regen_meta = user.owned_tools.get(self.META_ENERGY_REGEN_TS_KEY)
        if regen_meta is not None:
            regen_value = max(float(regen_meta), 0.0)
            if user.last_energy_regen_at != regen_value:
                user.last_energy_regen_at = regen_value
                changed = True

        if user.max_energy <= 0:
            user.max_energy = EXPEDITION_DEFAULT_MAX_ENERGY
            changed = True
        if user.energy < 0:
            user.energy = 0
            changed = True
        if user.energy > user.max_energy:
            user.energy = user.max_energy
            changed = True
        return changed

    def _store_progression_meta(self, user: UserState) -> None:
        user.owned_tools[self.META_XP_KEY] = max(user.xp, 0)
        user.owned_tools[self.META_LEVEL_KEY] = max(user.level, 0)
        user.owned_tools[self.META_CLAIM_MASK_KEY] = self._claimed_levels_to_mask(
            user.claimed_level_rewards
        )
        user.owned_tools[self.META_ENERGY_KEY] = max(user.energy, 0)
        user.owned_tools[self.META_MAX_ENERGY_KEY] = max(user.max_energy, 1)
        user.owned_tools[self.META_ENERGY_REGEN_TS_KEY] = max(float(user.last_energy_regen_at), 0.0)

    def _save_user(self, user: UserState) -> None:
        self._store_progression_meta(user)
        self.storage.save()

    def user(self, user_id: int) -> UserState:
        self.update_event_if_needed()
        user = self.storage.get_or_create_user(user_id)
        changed = self._load_progression_meta(user)
        changed = self._load_energy_meta(user) or changed
        changed = self.restore_energy_if_needed(user, save=False) or changed
        if changed:
            self._save_user(user)
        return user

    def restore_energy_if_needed(self, user: UserState, save: bool = False) -> bool:
        if user.max_energy <= 0:
            user.max_energy = EXPEDITION_DEFAULT_MAX_ENERGY
        if user.energy >= user.max_energy:
            return False

        current = now_ts()
        if user.last_energy_regen_at <= 0:
            user.last_energy_regen_at = current
            if save:
                self._save_user(user)
            return True

        elapsed = max(current - user.last_energy_regen_at, 0)
        regen_steps = int(elapsed // EXPEDITION_ENERGY_REGEN_SECONDS)
        if regen_steps <= 0:
            return False

        old_energy = user.energy
        user.energy = min(user.max_energy, user.energy + regen_steps)
        user.last_energy_regen_at += regen_steps * EXPEDITION_ENERGY_REGEN_SECONDS
        if user.energy >= user.max_energy:
            user.last_energy_regen_at = current

        changed = user.energy != old_energy
        if changed and save:
            self._save_user(user)
        return changed

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
        total = sum(max(float(chance), 0.0) for chance in weighted_map.values())
        if total <= 0:
            return next(iter(weighted_map))
        roll = random.uniform(0, total)
        cumulative = 0.0
        fallback = next(iter(weighted_map))
        for item_id, chance in weighted_map.items():
            if chance <= 0:
                continue
            cumulative += float(chance)
            if roll <= cumulative:
                return item_id
            fallback = item_id
        return fallback

    def _tree_weights_with_event(
        self, seed_trees: dict[str, float], event: dict[str, Any] | None
    ) -> dict[str, float]:
        if not event:
            return seed_trees
        bonuses = event.get("tree_bonus")
        if not isinstance(bonuses, dict):
            return seed_trees

        adjusted: dict[str, float] = {}
        for tree_id, chance in seed_trees.items():
            multiplier = max(self._safe_float(bonuses.get(tree_id), 1.0), 0.0)
            adjusted[tree_id] = max(float(chance), 0.0) * multiplier
        if sum(adjusted.values()) <= 0:
            return seed_trees
        return adjusted

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
        event = self.update_event_if_needed()
        if len(user.farm) >= MAX_FARM_SLOTS:
            return False, "Ферма заполнена. Сначала собери или убери растения."
        if user.seeds.get(seed_id, 0) <= 0:
            return False, "Нет купленных семян этого типа."

        seed_data = SEED_TYPES[seed_id]
        tree_weights = self._tree_weights_with_event(seed_data["trees"], event)
        tree_id = self._roll_weighted(tree_weights)
        tree_data = TREE_TYPES[tree_id]

        tool_pct = 0
        if user.active_tool and user.active_tool in TOOLS:
            tool_pct = TOOLS[user.active_tool]["reduction_pct"]

        base = tree_data["grow_seconds"]
        growth_bonus = max(self._safe_float((event or {}).get("growth_bonus"), 0.0), 0.0)
        event_growth_multiplier = max(1.0 - growth_bonus, 0.1)
        grow_seconds = max(int(base * (100 - tool_pct) / 100 * event_growth_multiplier), 60)
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
        event_note = ""
        if event and growth_bonus > 0:
            event_note = f"\n🔥 Ивент ускорил рост на {int(growth_bonus * 100)}%."
        xp_note = f"\n✨ XP: +{xp_result['xp_added']} ({xp_result['xp_total']} всего)"
        level_note = ""
        if xp_result["leveled_up"]:
            level_note = f"\n🎉 Уровень повышен: {xp_result['old_level']} → {xp_result['new_level']}"
        return True, f"Посажено: {seed_data['title']} → {tree_data['title']}{tool_note}{event_note}{xp_note}{level_note}"

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
        event = self.update_event_if_needed()
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
            "event": self._event_compact_view(event),
        }

    def get_farm_screen_state(self, user_id: int) -> dict:
        return self.get_farm_action_state(user_id)

    def _energy_eta_seconds(self, user: UserState) -> int:
        if user.energy >= user.max_energy:
            return 0
        anchor = user.last_energy_regen_at or now_ts()
        eta = int(anchor + EXPEDITION_ENERGY_REGEN_SECONDS - now_ts())
        return max(eta, 0)

    def _roll_expedition_loot(self) -> dict:
        roll = random.uniform(0, 100)
        cumulative = 0.0
        fallback = EXPEDITION_LOOT_TABLE[-1]
        for loot in EXPEDITION_LOOT_TABLE:
            cumulative += float(loot["chance"])
            if roll <= cumulative:
                return loot
            fallback = loot
        return fallback

    def get_expedition_state(self, user_id: int) -> dict:
        user = self.user(user_id)
        event = self.update_event_if_needed()
        return {
            "energy": user.energy,
            "max_energy": user.max_energy,
            "energy_cost": EXPEDITION_ENERGY_COST,
            "can_expedition": user.energy >= EXPEDITION_ENERGY_COST,
            "time_to_next": self._energy_eta_seconds(user),
            "event": self._event_compact_view(event),
        }

    def run_expedition(self, user_id: int) -> dict:
        user = self.user(user_id)
        event = self.update_event_if_needed()
        drop_bonus = max(self._safe_float((event or {}).get("drop_bonus"), 0.0), 0.0)
        self.restore_energy_if_needed(user, save=False)
        if user.energy < EXPEDITION_ENERGY_COST:
            return {
                "ok": False,
                "message": "⚡ Энергия закончилась. Подожди восстановления или вернись позже.",
                "state": self.get_expedition_state(user_id),
            }

        user.energy -= EXPEDITION_ENERGY_COST
        if user.energy < user.max_energy and user.last_energy_regen_at <= 0:
            user.last_energy_regen_at = now_ts()

        reward_cfg = self._roll_expedition_loot()
        reward_type = reward_cfg["type"]
        reward_amount = int(reward_cfg.get("amount", 1))
        reward_title = reward_cfg["title"]
        result = {"type": reward_type, "title": reward_title, "amount": reward_amount}

        if reward_type == "coins":
            coins = random.randint(int(reward_cfg["min"]), int(reward_cfg["max"]))
            if drop_bonus > 0:
                coins = max(int(coins * (1.0 + drop_bonus * 0.5)), coins)
            user.coins += coins
            result["amount"] = coins
            result["text"] = f"Найдено <code>{coins}</code> монет."
        elif reward_type == "seed":
            seed_id = reward_cfg["seed_id"]
            if drop_bonus > 0 and random.random() <= min(drop_bonus, 0.35):
                reward_amount += 1
            user.seeds[seed_id] = user.seeds.get(seed_id, 0) + reward_amount
            result["seed_id"] = seed_id
            result["amount"] = reward_amount
            result["text"] = f"Найдено {reward_title} x<code>{reward_amount}</code>."
        else:
            item_id = reward_cfg["item_id"]
            if drop_bonus > 0 and random.random() <= min(drop_bonus, 0.25):
                reward_amount += 1
            user.harvest[item_id] = user.harvest.get(item_id, 0) + reward_amount
            result["item_id"] = item_id
            result["amount"] = reward_amount
            result["text"] = f"Получен предмет {ITEM_TITLES.get(item_id, reward_title)} x<code>{reward_amount}</code>."

        self._save_user(user)
        return {"ok": True, "reward": result, "state": self.get_expedition_state(user_id)}

    def get_hub_state(self, user_id: int) -> dict:
        user = self.user(user_id)
        event = self.update_event_if_needed()
        farm_state = self.get_farm_action_state(user_id)
        expedition_state = self.get_expedition_state(user_id)
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
            "energy": expedition_state["energy"],
            "max_energy": expedition_state["max_energy"],
            "can_expedition": expedition_state["can_expedition"],
            "event": self._event_compact_view(event),
        }

    def get_player_hub_state(self, user_id: int) -> dict:
        return self.get_hub_state(user_id)

    def get_profile_state(self, user_id: int) -> dict:
        user = self.user(user_id)
        progress = self.get_level_progress(user_id)
        expedition = self.get_expedition_state(user_id)
        return {"user": user, "progress": progress, "expedition": expedition}
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

    def _roll_drop(self, tree_id: str, drop_bonus: float = 0.0) -> dict:
        drops = TREE_TYPES[tree_id]["drops"]
        adjusted_weights: list[float] = []
        for drop in drops:
            base_chance = max(self._safe_float(drop.get("chance"), 0.0), 0.0)
            rarity_multiplier = 2.0 if base_chance <= XP_REWARDS["rare_drop_threshold"] else 1.0
            adjusted_weights.append(base_chance * (1.0 + drop_bonus * rarity_multiplier))

        total = sum(adjusted_weights)
        if total <= 0:
            return drops[-1]
        roll = random.uniform(0, total)
        cumulative = 0.0
        fallback = drops[-1]
        for drop, weight in zip(drops, adjusted_weights):
            cumulative += weight
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
        event = self.update_event_if_needed()
        drop_bonus = max(self._safe_float((event or {}).get("drop_bonus"), 0.0), 0.0)
        extra_drop_cfg = (event or {}).get("extra_drop")
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
                drop = self._roll_drop(plant.tree_id, drop_bonus=drop_bonus)
                user.harvest[drop["id"]] = user.harvest.get(drop["id"], 0) + 1
                drop_price = int(max(self._safe_float(drop.get("price"), 0.0), 0.0))
                coin_gain = max(int(drop_price * (1.0 + drop_bonus)), drop_price)
                user.coins += coin_gain
                harvested += 1
                coins += coin_gain
                drops.append(drop["title"])
                gained_xp += self._xp_for_harvest(plant.tree_id, drop)

                if (
                    isinstance(extra_drop_cfg, dict)
                    and self.inventory_free(user) > 0
                    and random.random() <= max(self._safe_float(extra_drop_cfg.get("chance"), 0.0), 0.0)
                ):
                    extra_id = str(extra_drop_cfg.get("id", "")).strip()
                    if extra_id:
                        extra_title = str(extra_drop_cfg.get("title", extra_id)).strip()
                        user.harvest[extra_id] = user.harvest.get(extra_id, 0) + 1
                        drops.append(extra_title)
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
            "event": self._event_compact_view(event),
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
