from __future__ import annotations

import logging

from telegram import BotCommand, Update
from telegram.ext import Application, ContextTypes

from app.config import load_config
from app.data.constants import COMMANDS
from app.handlers import register_handlers
from app.services.anti_spam import AntiSpamService
from app.services.game_service import GameService
from app.utils.storage import Storage


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
    app.bot_data["config"] = cfg

    register_handlers(app)
    app.add_error_handler(error_handler)
    return app


def main() -> None:
    app = build_app()
    app.run_polling()


if __name__ == "__main__":
    main()
