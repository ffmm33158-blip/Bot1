from telegram import Update
from telegram.ext import CallbackContext
from app.data_store import DataStore


def stats_command(update: Update, context: CallbackContext, store: DataStore) -> None:
    user_id = str(update.effective_user.id)
    st = store.compute_stats(user_id)
    red = st["priorities"].get("red", 0)
    yellow = st["priorities"].get("yellow", 0)
    green = st["priorities"].get("green", 0)
    lines = [
        "📊 إحصائيات:",
        f"- إجمالي الملاحظات: {st['total_notes']}",
        f"- إجمالي التصنيفات: {st['total_categories']}",
        f"- الملاحظات الحديثة (آخر 7 أيام): {st['recent_count']}",
        "- تفصيل التصنيفات:",
    ]
    for cat_name, count in st["per_category"].items():
        lines.append(f"  • {cat_name}: {count}")
    lines += [
        "- توزيع الأولويات:",
        f"  • 🔴: {red}",
        f"  • 🟡: {yellow}",
        f"  • 🟢: {green}",
    ]
    update.message.reply_text("\n".join(lines))