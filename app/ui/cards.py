from __future__ import annotations

from app.data.constants import (
    INVENTORY_CAPACITY_LEVELS,
    ITEM_TITLES,
    MAX_FARM_SLOTS,
    MAX_LEVEL,
    SEED_TYPES,
    STATE_GROWING,
    STATE_READY,
    STATE_WILTED,
    TOOLS,
)
from app.data.models import UserState
from app.utils.time_utils import format_seconds

SEP = "━━━━━━━━━━━━━━━"


def energy_bar(current: int, max_energy: int) -> str:
    filled = "■" * max(min(current, max_energy), 0)
    empty = "□" * max(max_energy - current, 0)
    return f"<code>{filled}{empty}</code> <code>{current}/{max_energy}</code>"


def start_card(hub: dict) -> str:
    return (
        "<b>🌿 MemeGarden — игровой хаб</b>\n"
        f"{SEP}\n"
        f"💰 Баланс: <code>{hub['coins']}🪙</code>\n"
        f"📈 Уровень: <code>{hub['level']}</code> · XP: <code>{hub['xp']}</code>\n"
        f"⚡ Энергия: {energy_bar(hub['energy'], hub['max_energy'])}\n"
        f"🌱 Ферма: <code>{hub['farm_total']}/{MAX_FARM_SLOTS}</code> "
        f"(⏳ <code>{hub['farm_growing']}</code> · ✅ <code>{hub['farm_ready']}</code> · 🥀 <code>{hub['farm_wilted']}</code>)\n"
        f"🎒 Рюкзак: <code>{hub['inventory_used']}/{hub['inventory_capacity']}</code>\n\n"
        "<b>⬇️ Разделы — на нижней клавиатуре.</b>"
    )


def menu_hint_card(hub: dict) -> str:
    return (
        "<b>🏠 Главное меню</b>\n"
        f"{SEP}\n"
        f"💰 <code>{hub['coins']}🪙</code> · 📈 lvl <code>{hub['level']}</code> · ⚡ <code>{hub['energy']}/{hub['max_energy']}</code>\n"
        f"🌾 Ready на ферме: <code>{hub['farm_ready']}</code>\n"
        "Открой нужный раздел кнопками ниже или через inline-навигацию."
    )


def format_level_reward_lines(granted_rewards: list[dict]) -> str:
    if not granted_rewards:
        return ""

    lines = ["<b>🎁 Награды за уровень:</b>"]
    for reward in granted_rewards:
        parts = [f"lvl <code>{reward['level']}</code>"]
        if reward.get("coins", 0) > 0:
            parts.append(f"+<code>{reward['coins']}</code>🪙")

        seeds = reward.get("seeds", {})
        if seeds:
            seed_text = ", ".join(f"{SEED_TYPES.get(seed_id, {'title': seed_id})['title']} x{amount}" for seed_id, amount in seeds.items())
            parts.append(seed_text)

        tools = reward.get("tools", {})
        if tools:
            tool_text = ", ".join(
                f"{TOOLS.get(tool_id, {'title': tool_id})['title']} x{amount}" for tool_id, amount in tools.items()
            )
            parts.append(tool_text)

        if reward.get("inventory_capacity_bonus", 0) > 0:
            parts.append(f"+{reward['inventory_capacity_bonus']} к лимиту")

        lines.append("• " + " | ".join(parts))

    return "\n".join(lines)


def help_card() -> str:
    return (
        "<b>ℹ️ Помощь MemeGarden</b>\n"
        f"{SEP}\n"
        "Команды: <code>/start /help /shop /plant /farm /harvest /inventory /expedition /balance /level</code>\n"
        "Если интерфейс не обновился — нажми <b>🔄 Обновить</b> в нужном разделе."
    )


def shop_card() -> str:
    lines = [f"<b>🏪 Рынок MemeGarden</b>", SEP, "<b>🌱 Семена</b>"]
    for data in SEED_TYPES.values():
        lines.append(f"• {data['title']} — <code>{data['price']}🪙</code>")

    lines.extend(["", "<b>🛠 Инструменты</b>"])
    for data in TOOLS.values():
        lines.append(f"• {data['title']} — <code>{data['price']}🪙</code> (−{data['reduction_pct']}%)")
    return "\n".join(lines)


def level_card(state: UserState, level_progress: dict, expedition: dict) -> str:
    next_level = level_progress["next_level"]
    if next_level is None:
        progress_line = f"🏆 Максимальный уровень: <code>{MAX_LEVEL}</code>"
    else:
        progress_line = (
            f"До уровня <code>{next_level}</code>: <code>{level_progress['xp_to_next']}</code> XP"
            f" (порог: <code>{level_progress['next_level_xp']}</code>)"
        )

    return (
        "<b>👤 Профиль игрока</b>\n"
        f"{SEP}\n"
        f"📈 Уровень: <code>{state.level}</code>\n"
        f"✨ XP: <code>{state.xp}</code>\n"
        f"⚡ Энергия: {energy_bar(expedition['energy'], expedition['max_energy'])}\n"
        f"{progress_line}\n"
        f"🎁 Наград уровней получено: <code>{len(state.claimed_level_rewards)}</code>"
    )


def _progress_bar(progress: float, width: int = 10) -> str:
    filled = int(progress * width)
    return "🟩" * filled + "⬜" * (width - filled)


def farm_card(farm_rows: list[dict], action_state: dict) -> str:
    lines = [
        f"<b>🚜 Ферма</b> <code>{len(farm_rows)}/{MAX_FARM_SLOTS}</code>",
        f"{SEP}",
        f"⏳ <code>{action_state['farm_counts']['growing']}</code> · ✅ <code>{action_state['farm_counts']['ready']}</code> · 🥀 <code>{action_state['farm_counts']['wilted']}</code>",
    ]
    if not farm_rows:
        lines.append("\nФерма пока пустая. Загляни в рынок, купи семена и начни цикл роста.")

    for idx, row in enumerate(farm_rows, start=1):
        if row["state"] == STATE_GROWING:
            state_line = f"⏳ Растёт: <code>{format_seconds(row['time_left'])}</code>"
        elif row["state"] == STATE_READY:
            state_line = "✅ Готово к сбору"
        else:
            state_line = "🥀 Засохло"

        if row["state"] == STATE_GROWING:
            if row["next_boost_in"] > 0:
                next_boost = f"через <code>{format_seconds(row['next_boost_in'])}</code>"
            elif row["boost_used"] >= row["boost_max"]:
                next_boost = "лимит исчерпан"
            else:
                next_boost = "доступно"
        else:
            next_boost = "—"

        lines.extend(
            [
                f"\n<b>{idx}) #{row['plant_id']} {row['tree_title']}</b> · {row['rarity']}",
                f"🌰 {row['seed_title']}",
                f"📍 {state_line}",
                f"📊 {_progress_bar(row['progress'])}",
                f"⚡ <code>{row['boost_used']}/{row['boost_max']}</code> · {next_boost}",
                f"💰 Доход: ~<code>{row['approx_value']}🪙</code>",
            ]
        )
    return "\n".join(lines)


def inventory_card(state: UserState) -> str:
    seed_lines = [f"• {SEED_TYPES[s]['title']}: <code>{q}</code>" for s, q in state.seeds.items() if q > 0 and s in SEED_TYPES]
    crop_lines = [f"• {ITEM_TITLES.get(k, k)}: <code>{v}</code>" for k, v in state.harvest.items() if v > 0]
    active_tool = TOOLS[state.active_tool]["title"] if state.active_tool in TOOLS else "нет"
    used_slots = sum(state.harvest.values())

    return (
        "<b>🎒 Рюкзак</b>\n"
        f"{SEP}\n"
        f"📦 Предметы: <code>{used_slots}/{state.inventory_capacity}</code> (этапы: {', '.join(map(str, INVENTORY_CAPACITY_LEVELS))})\n"
        f"🛠 Активный инструмент: {active_tool}\n\n"
        + "<b>🌱 Семена</b>\n"
        + ("\n".join(seed_lines) if seed_lines else "(пусто)")
        + "\n\n<b>🌾 Дроп и предметы</b>\n"
        + ("\n".join(crop_lines) if crop_lines else "(пусто)")
    )


def tools_card(state: UserState) -> str:
    active_tool = TOOLS[state.active_tool]["title"] if state.active_tool in TOOLS else "нет"
    lines = ["<b>🛠 Инструменты</b>", SEP, f"Активный: <code>{active_tool}</code>", ""]
    owned_lines = [
        f"• {TOOLS[tool_id]['title']} x<code>{qty}</code>"
        for tool_id, qty in state.owned_tools.items()
        if qty > 0 and tool_id in TOOLS
    ]
    lines.append("<b>Коллекция:</b>\n" + ("\n".join(owned_lines) if owned_lines else "(пусто)"))
    return "\n".join(lines)


def expedition_card(expedition: dict, hub: dict) -> str:
    regen_note = "Энергия полная. Можно идти в поход." if expedition["time_to_next"] == 0 else f"До +1 энергии: <code>{format_seconds(expedition['time_to_next'])}</code>"
    return (
        "<b>🧭 Экспедиция</b>\n"
        f"{SEP}\n"
        f"⚡ Энергия: {energy_bar(expedition['energy'], expedition['max_energy'])}\n"
        f"💰 Баланс: <code>{hub['coins']}🪙</code>\n"
        f"🎒 Рюкзак: <code>{hub['inventory_used']}/{hub['inventory_capacity']}</code>\n"
        f"⏱ {regen_note}\n\n"
        "Отправляйся в экспедицию, чтобы найти монеты, семена и редкие подарки."
    )


def expedition_result_card(result: dict) -> str:
    reward = result["reward"]
    state = result["state"]
    return (
        "<b>🧭 Экспедиция завершена</b>\n"
        f"{SEP}\n"
        f"🎉 {reward['text']}\n"
        f"⚡ Осталось энергии: {energy_bar(state['energy'], state['max_energy'])}"
    )
