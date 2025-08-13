from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, MessageHandler, Filters, CommandHandler
from app.data_store import DataStore

ASK_QUERY = 1


def start_search(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("أدخل كلمات البحث 🔍:")
    return ASK_QUERY


def receive_query(update: Update, context: CallbackContext, store: DataStore) -> int:
    user_id = str(update.effective_user.id)
    q = update.message.text.strip()
    results = store.search_notes(user_id, q)
    if not results:
        update.message.reply_text("لا توجد نتائج.")
        return ConversationHandler.END
    lines = [f"نتائج البحث: {len(results)}"]
    for i, (n, c) in enumerate(results[:10], start=1):
        title = n.get("title", "") or "(بدون عنوان)"
        lines.append(f"{i}. 🎯 {title} — 📁 {c['name']} | #ID: {n['id']}")
    update.message.reply_text("\n".join(lines))
    return ConversationHandler.END


def cancel_search(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("تم الإلغاء.")
    return ConversationHandler.END


def build_search_handler(store: DataStore) -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("search", start_search)],
        states={
            ASK_QUERY: [MessageHandler(Filters.text & ~Filters.command, lambda u, c: receive_query(u, c, store))],
        },
        fallbacks=[CommandHandler("cancel", cancel_search)],
        name="search_conversation",
        persistent=False,
    )