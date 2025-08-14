from telegram.ext import MessageHandler, filters
from data_store import DataStore

def build_search_handler(store: DataStore):
    async def search_handler(update, context):
        # سيتم تطويرها لاحقاً
        await update.message.reply_text("ميزة البحث قيد التطوير...")
    
    return MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler)
