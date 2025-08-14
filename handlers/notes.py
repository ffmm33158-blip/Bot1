from telegram import Update
from telegram.ext import ContextTypes
from data_store import DataStore

async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE, store: DataStore) -> None:
    user_id = str(update.effective_user.id)
    notes = store.get_user_notes(user_id)
    
    if not notes:
        await update.message.reply_text("لا توجد ملاحظات لديك. استخدم /add لإضافة ملاحظة جديدة!")
        return
    
    notes_text = "�� ملاحظاتك:\n\n"
    for note in notes:
        priority_icon = "��" if note["priority"] == "red" else ("��" if note["priority"] == "yellow" else "🟢")
        notes_text += f"{priority_icon} **{note['title']}**\n"
        notes_text += f"   {note['text'][:50]}{'...' if len(note['text']) > 50 else ''}\n"
        notes_text += f"   ID: {note['id']}\n\n"
    
    await update.message.reply_text(notes_text, parse_mode='Markdown')
