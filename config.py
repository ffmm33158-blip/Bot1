# -*- coding: utf-8 -*-
"""
ملف إعدادات بوت تنظيم الملاحظات
"""

import os
from datetime import datetime

# إعدادات البوت
BOT_TOKEN = "8078959273:AAF5Y5F1mzNDIfPOdb3GWhzary6-vKhtUWY"

# إعدادات البيانات
DATA_FILE = "notes_data.json"
BACKUP_DIR = "/tmp"

# إعدادات الخادم
PORT = int(os.environ.get('PORT', 8000))
HOST = "0.0.0.0"

# إعدادات التصنيفات الافتراضية
DEFAULT_CATEGORIES = [
    "عام",
    "مهام", 
    "أفكار"
]

# إعدادات الأولويات
PRIORITIES = {
    "🔴": "مهم جداً",
    "🟡": "مهم",
    "🟢": "عادي"
}

# إعدادات التذكيرات السريعة
QUICK_REMINDERS = {
    "30min": "بعد 30 دقيقة",
    "1hour": "بعد ساعة",
    "2hours": "بعد ساعتين", 
    "6hours": "بعد 6 ساعات",
    "tomorrow_9am": "غداً 9 صباحاً",
    "tomorrow_6pm": "غداً 6 مساءً"
}

# إعدادات الأيام للتذكيرات المخصصة
CUSTOM_DAYS = {
    "today": "اليوم",
    "tomorrow": "غداً",
    "day_after": "بعد غد",
    "next_week": "الأسبوع القادم"
}

# إعدادات العرض
MAX_NOTES_PER_CATEGORY = 5
MAX_SEARCH_RESULTS = 10
MAX_TITLE_PREVIEW = 30
MAX_TEXT_PREVIEW = 50

# إعدادات النسخ الاحتياطي
BACKUP_FILENAME_FORMAT = "notes_backup_{timestamp}.txt"
BACKUP_DATE_FORMAT = "%Y%m%d_%H%M%S"

# رسائل النظام
MESSAGES = {
    "welcome": """
🚀 **مرحباً بك في بوت تنظيم الملاحظات الذكي!**

📋 **الأوامر المتاحة:**

➕ `/add` - إضافة ملاحظة أو تصنيف جديد
📚 `/notes` - عرض جميع الملاحظات
✏️ `/edit` - تعديل الملاحظات والتصنيفات
🔍 `/search` - البحث في الملاحظات
📊 `/stats` - إحصائيات شاملة
💾 `/backup` - إنشاء نسخة احتياطية
📋 `/menu` - قائمة الأوامر

🎯 **المميزات:**
• نظام تصنيفات مرن
• أولويات ملونة (🔴🟡🟢)
• تذكيرات ذكية
• واجهة أزرار تفاعلية
• حفظ آمن للبيانات

ابدأ باستخدام `/add` لإضافة ملاحظتك الأولى! ✨
    """,
    
    "menu": """
📋 **قائمة الأوامر الشاملة:**

🚀 **الأوامر الأساسية:**
• `/start` - بدء البوت والتعرف على المميزات
• `/menu` - عرض هذه القائمة

📝 **إدارة الملاحظات:**
• `/add` - إضافة ملاحظة أو تصنيف جديد
• `/notes` - عرض جميع الملاحظات منظمة
• `/edit` - تعديل الملاحظات والتصنيفات
• `/search` - البحث المتقدم في الملاحظات

📊 **المتابعة والتحليل:**
• `/stats` - إحصائيات تفصيلية شاملة
• `/backup` - إنشاء نسخة احتياطية كاملة

💡 **نصائح الاستخدام:**
• استخدم `/add` لإضافة ملاحظتك الأولى
• استخدم `/notes` لمراجعة ملاحظاتك
• استخدم `/search` للعثور على ملاحظات محددة
• استخدم `/stats` لمتابعة تقدمك
• استخدم `/backup` للحفاظ على أمان بياناتك

🎯 **ابدأ الآن باستخدام `/add`!**
    """,
    
    "no_notes": "📝 لا توجد ملاحظات بعد. استخدم `/add` لإضافة ملاحظتك الأولى!",
    "operation_cancelled": "تم إلغاء العملية ❌",
    "note_added_success": "✅ **تم إضافة الملاحظة بنجاح!**",
    "category_added_success": "✅ تم إضافة التصنيف '{name}' بنجاح!\n🆔 رقم التصنيف: #{id}",
    "backup_success": "💾 **نسخة احتياطية كاملة من الملاحظات**"
}

# رسائل الأخطاء
ERROR_MESSAGES = {
    "save_note": "❌ خطأ في حفظ الملاحظة: {error}",
    "backup": "❌ خطأ في إنشاء النسخة الاحتياطية: {error}",
    "web_server": "خطأ في خادم الويب: {error}",
    "bot_start": "خطأ في تشغيل البوت: {error}",
    "invalid_token": "❌ يرجى وضع توكن البوت الصحيح!"
}

# إعدادات التسجيل
LOGGING_CONFIG = {
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "level": "INFO"
}

# إعدادات الويب
WEB_PAGES = {
    "main": """
    <html>
    <head>
        <title>Notes Bot</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; text-align: center; }}
            .status {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 بوت تنظيم الملاحظات يعمل!</h1>
            <div class="status">
                <p>✅ البوت نشط ويعمل بشكل طبيعي</p>
                <p>📅 الوقت: {timestamp}</p>
            </div>
            <div class="info">
                <p>📝 عدد الملاحظات: {notes_count}</p>
                <p>📁 عدد التصنيفات: {categories_count}</p>
                <p>🌐 الخادم: Render</p>
            </div>
        </div>
    </body>
    </html>
    """
}

def get_current_timestamp():
    """الحصول على الوقت الحالي"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def format_backup_filename():
    """تنسيق اسم ملف النسخة الاحتياطية"""
    timestamp = datetime.now().strftime(BACKUP_DATE_FORMAT)
    return BACKUP_FILENAME_FORMAT.format(timestamp=timestamp)