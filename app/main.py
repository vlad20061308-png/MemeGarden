from __future__ import annotations

import logging

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from app.config import load_config
from app.data.constants import COMMANDS
from app.data.storage import Storage
from app.handlers import (
    balance_handler,
    farm_handler,
    harvest_handler,
    help_handler,
    inventory_handler,
    noop_callback,
    plant_handler,
    plant_seed_callback,
    shop_buy_callback,
    shop_handler,
    start_handler,
)
from app.services.anti_spam import AntiSpamService
from app.services.game_service import GameService


logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO
)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([BotCommand(cmd, desc) for cmd, desc in COMMANDS])


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.exception("Exception while handling update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Попробуй позже.")


def build_app() -> Application:
    cfg = load_config()
    storage = Storage(cfg.data_file)
    game = GameService(storage)
    anti_spam = AntiSpamService(cfg.anti_spam_seconds)

    app = Application.builder().token(cfg.bot_token).post_init(post_init).build()

    app.bot_data["game"] = game
    app.bot_data["anti_spam"] = anti_spam

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("shop", shop_handler))
    app.add_handler(CommandHandler("plant", plant_handler))
    app.add_handler(CommandHandler("farm", farm_handler))
    app.add_handler(CommandHandler("harvest", harvest_handler))
    app.add_handler(CommandHandler("inventory", inventory_handler))
    app.add_handler(CommandHandler("balance", balance_handler))

    app.add_handler(CallbackQueryHandler(shop_buy_callback, pattern=r"^shop_buy:"))
    app.add_handler(CallbackQueryHandler(plant_seed_callback, pattern=r"^plant_seed:"))
    app.add_handler(CallbackQueryHandler(noop_callback, pattern=r"^noop$"))
    app.add_error_handler(error_handler)
    return app


def main() -> None:
    app = build_app()
    app.run_polling()


if __name__ == "__main__":
    main()
