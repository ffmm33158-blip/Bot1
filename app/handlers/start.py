from telegram import Update, ParseMode
from telegram.ext import CallbackContext

WELCOME = (
    "مرحبا! 👋\n\n"
    "أنا بوت ذكي لتنظيم وإدارة ملاحظاتك عبر تليجرام.\n"
    "إليك الأوامر المتاحة:\n\n"
    "1) /start 🚀 — تنشيط البوت وعرض دليل البدء\n"
    "2) /add ➕ — إضافة ملاحظة أو تصنيف\n"
    "3) /notes 📚 — عرض الملاحظات حسب التصنيفات\n"
    "4) /edit ✏️ — تعديل الملاحظات والتصنيفات\n"
    "5) /search 🔍 — البحث المتقدم\n"
    "6) /stats 📊 — إحصائيات تفصيلية\n"
    "7) /backup 💾 — إنشاء نسخة احتياطية\n"
    "8) /menu 📋 — عرض قائمة الأوامر\n\n"
    "نصائح:\n- استخدم التصنيفات لتنظيم أفكارك\n- فعّل التذكيرات للمهام المهمة\n- جرّب البحث للوصول السريع"
)


def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(WELCOME)


def menu_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(WELCOME)