import logging
import os
import signal
from typing import Dict, Any
from telegram import Update, Bot
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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # تحديث الدالة لتكون async
    pass

async def main() -> None:
    token = "8078959273:AAHMohcrqF3YcSpBwUZAaDAqSKoWM-wfpZg"
    
    application = Application.builder().token(token).build()
    
    # إضافة handlers
    application.add_handler(CommandHandler("start", start_command))
    
    logger.info("Bot started successfully!")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
