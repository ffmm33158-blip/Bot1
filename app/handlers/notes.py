from typing import List, Dict
from telegram import Update
from telegram.ext import CallbackContext
from app.data_store import DataStore


def format_note_line(note: Dict) -> str:
    prio = note.get("priority", "green")
    icon = "🔴" if prio == "red" else ("🟡" if prio == "yellow" else "🟢")
    title = note.get("title", "").strip() or "(بدون عنوان)"
    text = note.get("text", "")
    preview = (text[:30] + "...") if len(text) > 30 else text
    return f"{icon} {title} - {preview} | #ID: {note.get('id')}"


def notes_command(update: Update, context: CallbackContext, store: DataStore) -> None:
    user_id = str(update.effective_user.id)
    grouped = store.list_notes_by_category(user_id)
    cats = store.list_categories(user_id)
    lines: List[str] = []
    for c in cats:
        cat_id = c["id"]
        notes = grouped.get(cat_id, [])
        if not notes:
            continue
        lines.append(f"📁 {c['name']} ({len(notes)})")
        for n in notes[:5]:
            lines.append("- " + format_note_line(n))
        if len(notes) > 5:
            lines.append(f"… وهناك {len(notes)-5} ملاحظة إضافية")
        lines.append("")
    if not lines:
        update.message.reply_text("لا توجد ملاحظات بعد. استخدم /add لإضافة أول ملاحظة.")
        return
    text = "\n".join(lines).strip()
    update.message.reply_text(text)