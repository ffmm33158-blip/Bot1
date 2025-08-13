import io
from datetime import datetime, timezone
from telegram import Update, InputFile
from telegram.ext import CallbackContext
from app.data_store import DataStore


def backup_command(update: Update, context: CallbackContext, store: DataStore) -> None:
    user_id = str(update.effective_user.id)
    user = store.get_user_data(user_id)
    categories = user.get("categories", [])
    notes = user.get("notes", [])
    cat_by_id = {c["id"]: c["name"] for c in categories}
    created = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    buf = io.StringIO()
    buf.write(f"Backup created at: {created}\n")
    buf.write(f"Total notes: {len(notes)}\n\n")
    for c in categories:
        buf.write(f"## {c['name']}\n")
        cat_notes = [n for n in notes if n["category_id"] == c["id"]]
        for n in cat_notes:
            pr = n.get("priority", "green")
            icon = "🔴" if pr == "red" else ("🟡" if pr == "yellow" else "🟢")
            buf.write(f"[{icon}] {n['title']} (ID {n['id']})\n")
            buf.write(n.get("text", "") + "\n")
            buf.write(f"Created: {n.get('created_at', '')}\n")
            buf.write("\n")
        buf.write("\n")

    buf.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"notes_backup_{ts}.txt"
    update.message.reply_document(document=InputFile(buf, filename=filename), filename=filename)