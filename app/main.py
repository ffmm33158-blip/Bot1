import logging
import os
import signal
from typing import Dict, Any
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from app.data_store import DataStore
from app.scheduler import ReminderScheduler
from app.web_server import create_app
from app.handlers.start import start_command, menu_command
from app.handlers.notes import notes_command
from app.handlers.stats import stats_command
from app.handlers.backup import backup_command
from app.handlers.search import build_search_handler
from app.handlers.add import build_add_handler
from app.handlers.edit import build_edit_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def build_status_provider(store: DataStore):
    def provider() -> Dict[str, Any]:
        data = store._read()
        total_users = len(data.get("users", {}))
        total_notes = sum(len(u.get("notes", [])) for u in data.get("users", {}).values())
        return {"users": total_users, "notes": total_notes}
    return provider


def send_reminder_callback(bot: Bot, store: DataStore, user_id: int, note_id: int) -> None:
    try:
        note = store.get_note(str(user_id), note_id)
        if not note:
            return
        pr = note.get("priority", "green")
        icon = "🔴" if pr == "red" else ("🟡" if pr == "yellow" else "🟢")
        title = note.get("title", "") or "(بدون عنوان)"
        text = note.get("text", "")
        msg = f"⏰ تذكير!\n{icon} {title}\n{text}\n#ID: {note_id}"
        bot.send_message(chat_id=user_id, text=msg)
    except Exception:
        logger.exception("Failed to send reminder")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    store = DataStore()
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    scheduler = ReminderScheduler()
    scheduler.set_send_callback(lambda uid, nid: send_reminder_callback(updater.bot, store, uid, nid))

    dispatcher.bot_data["store"] = store
    dispatcher.bot_data["scheduler"] = scheduler

    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("menu", menu_command))
    dispatcher.add_handler(CommandHandler("notes", lambda u, c: notes_command(u, c, store)))
    dispatcher.add_handler(CommandHandler("stats", lambda u, c: stats_command(u, c, store)))
    dispatcher.add_handler(CommandHandler("backup", lambda u, c: backup_command(u, c, store)))
    dispatcher.add_handler(build_search_handler(store))
    dispatcher.add_handler(build_add_handler(store))
    dispatcher.add_handler(build_edit_handler(store))

    mode = os.getenv("MODE", "polling").lower()

    def graceful_stop(signum, frame):
        logger.info("Shutting down...")
        scheduler.shutdown()
        updater.stop()

    signal.signal(signal.SIGTERM, graceful_stop)
    signal.signal(signal.SIGINT, graceful_stop)

    if mode == "webhook":
        webhook_url = os.getenv("WEBHOOK_URL")
        if not webhook_url:
            raise RuntimeError("WEBHOOK_URL must be set in webhook mode")
        status_provider = build_status_provider(store)

        def webhook_handler(payload: dict) -> None:
            try:
                update = Update.de_json(payload, updater.bot)
                updater.dispatcher.process_update(update)
            except Exception:
                logger.exception("Error processing webhook update")

        app = create_app(status_provider, webhook_handler)
        port = int(os.getenv("PORT", "8080"))
        host = "0.0.0.0"
        # Set Telegram webhook to our Flask endpoint path
        updater.bot.set_webhook(f"{webhook_url}/telegram/webhook/{token}")
        logger.info("Webhook set to %s/telegram/webhook/%s", webhook_url, token)
        app.run(host=host, port=port)
    else:
        status_provider = build_status_provider(store)
        app = create_app(status_provider)

        from threading import Thread
        port = int(os.getenv("PORT", "8080"))
        host = "0.0.0.0"
        t = Thread(target=lambda: app.run(host=host, port=port), daemon=True)
        t.start()

        updater.start_polling(clean=True)
        updater.idle()


if __name__ == "__main__":
    main()