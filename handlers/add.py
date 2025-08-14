from telegram.ext import MessageHandler, filters
from data_store import DataStore

def build_add_handler(store: DataStore):
    async def add_handler(update, context):
        # سيتم تطويرها لاحقاً
        await update.message.reply_text("ميزة الإضافة قيد التطوير...")
    
    return MessageHandler(filters.TEXT & ~filters.COMMAND, add_handler)
