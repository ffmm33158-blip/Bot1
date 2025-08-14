from telegram.ext import MessageHandler, filters
from data_store import DataStore

def build_edit_handler(store: DataStore):
    async def edit_handler(update, context):
        # سيتم تطويرها لاحقاً
        await update.message.reply_text("ميزة التعديل قيد التطوير...")
    
    return MessageHandler(filters.TEXT & ~filters.COMMAND, edit_handler)
