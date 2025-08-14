from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_main_menu_keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_text = f"""
مرحباً {user.first_name}! 👋

أنا بوت تنظيم الملاحظات الخاص بك 📝
يمكنني مساعدتك في:
• 📝 إضافة ملاحظات جديدة
• 🗂️ تنظيم ملاحظاتك
• ⏰ إعداد تذكيرات
• �� البحث في الملاحظات

اضغط على "القائمة الرئيسية" للبدء!
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "القائمة الرئيسية:",
        reply_markup=get_main_menu_keyboard()
    )
