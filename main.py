import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

load_dotenv()

# Constants
DATA_FILE = os.getenv("NOTES_DATA_FILE", "notes_data.json")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class DataStore:
    """Simple JSON-backed data store for notes and categories."""

    def __init__(self, path: str):
        self.path = path
        self.data = {"categories": {"عام": []}, "notes": []}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error("Failed to load data file: %s", e)
        else:
            self._save()

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Failed to save data file: %s", e)

    # Category management
    def get_categories(self):
        return list(self.data.get("categories", {}).keys())

    def add_category(self, name: str):
        if name not in self.data["categories"]:
            self.data["categories"][name] = []
            self._save()

    # Note management (simplified)
    def add_note(self, category: str, title: str, text: str, priority: str):
        note_id = len(self.data["notes"]) + 1
        note = {
            "id": note_id,
            "category": category,
            "title": title,
            "text": text,
            "priority": priority,
            "created": datetime.utcnow().isoformat(),
        }
        self.data["notes"].append(note)
        # Link note id to category list
        self.data["categories"].setdefault(category, []).append(note_id)
        self._save()
        return note_id


db = DataStore(DATA_FILE)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with all commands."""
    welcome_text = (
        "مرحبا بك في بوت تنظيم الملاحظات!\n\n"
        "اختر أمرا من الأزرار أو اطلع على القائمة:\n"
    )
    keyboard = [
        [
            InlineKeyboardButton("➕ إضافة", callback_data="add"),
            InlineKeyboardButton("📚 الملاحظات", callback_data="notes"),
        ],
        [
            InlineKeyboardButton("✏️ تعديل", callback_data="edit"),
            InlineKeyboardButton("🔍 بحث", callback_data="search"),
        ],
        [
            InlineKeyboardButton("📊 إحصائيات", callback_data="stats"),
            InlineKeyboardButton("💾 نسخة احتياطية", callback_data="backup"),
        ],
        [InlineKeyboardButton("📋 قائمة", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_command(update, context)


def main():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment variables.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))

    logger.info("Bot starting...")
    application.run_polling()


if __name__ == "__main__":
    main()
