from telegram import Update
from telegram.ext import ContextTypes
from data_store import DataStore

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE, store: DataStore) -> None:
    user_id = str(update.effective_user.id)
    notes = store.get_user_notes(user_id)
    
    if not notes:
        await update.message.reply_text("لا توجد ملاحظات للنسخ الاحتياطي!")
        return
    
    backup_text = f"""
�� النسخ الاحتياطي:

📅 تاريخ النسخ: {datetime.now().strftime('%Y-%m-%d')}
📝 عدد الملاحظات: {len(notes)}
📋 الملاحظات:
"""
    
    for note in notes:
        backup_text += f"\n🔸 {note['title']}\n   {note['text']}\n"
    
    # تقسيم الرسالة إذا كانت طويلة
    if len(backup_text) > 4000:
        parts = [backup_text[i:i+4000] for i in range(0, len(backup_text), 4000)]
        for i, part in enumerate(parts):
            await update.message.reply_text(f"جزء {i+1} من {len(parts)}:\n{part}")
    else:
        await update.message.reply_text(backup_text)
