from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from app.handlers.callback_handlers import (
    drop_item_callback,
    equip_tool_callback,
    farm_boost_callback,
    farm_harvest_callback,
    farm_refresh_callback,
    menu_back_callback,
    noop_callback,
    plant_seed_callback,
    shop_buy_seed_callback,
    shop_buy_tool_callback,
    shop_section_callback,
)
from app.handlers.command_handlers import (
    balance_handler,
    farm_handler,
    harvest_handler,
    help_handler,
    inventory_handler,
    plant_handler,
    shop_handler,
    start_handler,
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

    app.add_handler(CallbackQueryHandler(shop_buy_seed_callback, pattern=r"^shop_buy_seed:"))
    app.add_handler(CallbackQueryHandler(shop_buy_tool_callback, pattern=r"^shop_buy_tool:"))
    app.add_handler(CallbackQueryHandler(shop_section_callback, pattern=r"^shop_section:"))
    app.add_handler(CallbackQueryHandler(plant_seed_callback, pattern=r"^plant_seed:"))
    app.add_handler(CallbackQueryHandler(farm_boost_callback, pattern=r"^farm_boost:"))
    app.add_handler(CallbackQueryHandler(farm_harvest_callback, pattern=r"^farm_harvest$"))
    app.add_handler(CallbackQueryHandler(farm_refresh_callback, pattern=r"^farm_refresh$"))
    app.add_handler(CallbackQueryHandler(equip_tool_callback, pattern=r"^equip_tool:"))
    app.add_handler(CallbackQueryHandler(drop_item_callback, pattern=r"^drop_item:"))
    app.add_handler(CallbackQueryHandler(menu_back_callback, pattern=r"^menu_back$"))
    app.add_handler(CallbackQueryHandler(noop_callback, pattern=r"^noop$"))
