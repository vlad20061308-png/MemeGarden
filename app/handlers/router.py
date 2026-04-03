from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from app.handlers.callback_handlers import (
    dev_add_1000_callback,
    dev_ready_all_callback,
    dev_set_100000_callback,
    dev_state_refresh_callback,
    dev_wilt_all_callback,
    drop_item_callback,
    equip_tool_callback,
    farm_boost_callback,
    farm_harvest_callback,
    farm_refresh_callback,
    menu_open_callback,
    menu_back_callback,
    noop_callback,
    plant_seed_callback,
    shop_buy_seed_callback,
    shop_buy_tool_callback,
    shop_section_callback,
)
from app.handlers.command_handlers import (
    balance_handler,
    dev_balance_add_handler,
    dev_balance_set_handler,
    dev_balance_take_handler,
    dev_ready_handler,
    dev_ready_one_handler,
    dev_state_handler,
    dev_wilt_handler,
    farm_handler,
    harvest_handler,
    help_handler,
    inventory_handler,
    level_handler,
    menu_handler,
    plant_handler,
    shop_handler,
    start_handler,
    tools_handler,
)


def register_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("shop", shop_handler))
    app.add_handler(CommandHandler("plant", plant_handler))
    app.add_handler(CommandHandler("farm", farm_handler))
    app.add_handler(CommandHandler("harvest", harvest_handler))
    app.add_handler(CommandHandler("inventory", inventory_handler))
    app.add_handler(CommandHandler("balance", balance_handler))
    app.add_handler(CommandHandler("level", level_handler))
    app.add_handler(CommandHandler("menu", menu_handler))
    app.add_handler(CommandHandler("tools", tools_handler))
    app.add_handler(CommandHandler("dev_ready", dev_ready_handler))
    app.add_handler(CommandHandler("dev_ready_one", dev_ready_one_handler))
    app.add_handler(CommandHandler("dev_wilt", dev_wilt_handler))
    app.add_handler(CommandHandler("dev_balance_set", dev_balance_set_handler))
    app.add_handler(CommandHandler("dev_balance_add", dev_balance_add_handler))
    app.add_handler(CommandHandler("dev_balance_take", dev_balance_take_handler))
    app.add_handler(CommandHandler("dev_state", dev_state_handler))

    app.add_handler(CallbackQueryHandler(shop_buy_seed_callback, pattern=r"^shop_buy_seed:"))
    app.add_handler(CallbackQueryHandler(shop_buy_tool_callback, pattern=r"^shop_buy_tool:"))
    app.add_handler(CallbackQueryHandler(shop_section_callback, pattern=r"^shop_section:"))
    app.add_handler(CallbackQueryHandler(menu_open_callback, pattern=r"^menu_open:"))
    app.add_handler(CallbackQueryHandler(plant_seed_callback, pattern=r"^plant_seed:"))
    app.add_handler(CallbackQueryHandler(farm_boost_callback, pattern=r"^farm_boost:"))
    app.add_handler(CallbackQueryHandler(farm_harvest_callback, pattern=r"^farm_harvest$"))
    app.add_handler(CallbackQueryHandler(farm_refresh_callback, pattern=r"^farm_refresh$"))
    app.add_handler(CallbackQueryHandler(equip_tool_callback, pattern=r"^equip_tool:"))
    app.add_handler(CallbackQueryHandler(drop_item_callback, pattern=r"^drop_item:"))
    app.add_handler(CallbackQueryHandler(menu_back_callback, pattern=r"^menu_back$"))
    app.add_handler(CallbackQueryHandler(noop_callback, pattern=r"^noop$"))
    app.add_handler(CallbackQueryHandler(dev_ready_all_callback, pattern=r"^dev_ready_all$"))
    app.add_handler(CallbackQueryHandler(dev_wilt_all_callback, pattern=r"^dev_wilt_all$"))
    app.add_handler(CallbackQueryHandler(dev_add_1000_callback, pattern=r"^dev_add_1000$"))
    app.add_handler(CallbackQueryHandler(dev_set_100000_callback, pattern=r"^dev_set_100000$"))
    app.add_handler(CallbackQueryHandler(dev_state_refresh_callback, pattern=r"^dev_state_refresh$"))
