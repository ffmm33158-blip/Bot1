from telegram import Update
from telegram.ext import ContextTypes

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

استخدم الأوامر التالية:
/start - البداية
/menu - القائمة
/notes - عرض الملاحظات
/stats - الإحصائيات
/backup - النسخ الاحتياطي
"""
    
    await update.message.reply_text(welcome_text)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    menu_text = """
📋 القائمة الرئيسية:

�� /add - إضافة ملاحظة جديدة
📋 /notes - عرض جميع الملاحظات
�� /search - البحث في الملاحظات
�� /stats - إحصائياتك
�� /backup - نسخ احتياطي
"""
    
    await update.message.reply_text(menu_text)
