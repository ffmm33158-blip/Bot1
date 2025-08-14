import logging
import os
import asyncio
from typing import Dict, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from data_store import DataStore
from scheduler import ReminderScheduler
from web_server import create_app
from handlers.start import start_command, menu_command
from handlers.notes import notes_command
from handlers.stats import stats_command
from handlers.backup import backup_command
from handlers.search import build_search_handler
from handlers.add import build_add_handler
from handlers.edit import build_edit_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

def build_status_provider(store: DataStore):
    def provider() -> Dict[str, Any]:
        data = store._read()
        total_users = len(data.get("users", {}))
        total_notes = sum(len(u.get("notes", [])) for u in data.get("users", {}).values())
        return {"users": total_users, "notes": total_notes}
    return provider

async def send_reminder_callback(bot, store: DataStore, user_id: int, note_id: int) -> None:
    try:
        note = store.get_note(str(user_id), note_id)
        if not note:
            return
        pr = note.get("priority", "red")
        icon = "🔴" if pr == "red" else ("��" if pr == "yellow" else "🟢")
        title = note.get("title", "") or "(بدون عنوان)"
        text = note.get("text", "")
        msg = f"⏰ تذكير!\n{icon} {title}\n{text}\n#ID: {note_id}"
        await bot.send_message(chat_id=user_id, text=msg)
    except Exception:
        logger.exception("Failed to send reminder")

async def main() -> None:
    token = "8078959273:AAHMohcrqF3YcSpBwUZAaDAqSKoWM-wfpZg"
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    store = DataStore()
    application = Application.builder().token(token).build()

    scheduler = ReminderScheduler()
    scheduler.set_send_callback(lambda uid, nid: asyncio.create_task(send_reminder_callback(application.bot, store, uid, nid)))

    # إضافة handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("notes", lambda u, c: notes_command(u, c, store)))
    application.add_handler(CommandHandler("stats", lambda u, c: stats_command(u, c, store)))
    application.add_handler(CommandHandler("backup", lambda u, c: backup_command(u, c, store)))
    application.add_handler(build_search_handler(store))
    application.add_handler(build_add_handler(store))
    application.add_handler(build_edit_handler(store))

    logger.info("Bot started successfully!")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
