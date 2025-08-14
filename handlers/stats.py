from telegram import Update
from telegram.ext import ContextTypes
from data_store import DataStore

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE, store: DataStore) -> None:
    user_id = str(update.effective_user.id)
    notes = store.get_user_notes(user_id)
    
    total_notes = len(notes)
    red_priority = len([n for n in notes if n["priority"] == "red"])
    yellow_priority = len([n for n in notes if n["priority"] == "yellow"])
    green_priority = len([n for n in notes if n["priority"] == "green"])
    
    stats_text = f"""
📊 إحصائياتك:

📝 إجمالي الملاحظات: {total_notes}
 أولوية عالية: {red_priority}
🟡 أولوية متوسطة: {yellow_priority}
🟢 أولوية منخفضة: {green_priority}
"""
    
    await update.message.reply_text(stats_text)
