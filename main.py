import os
import json
import logging
import http.server
import socketserver
import threading
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# رمز البوت
BOT_TOKEN = "8078959273:AAF5Y5F1mzNDIfPOdb3GWhzary6-vKhtUWY"

# حالات المحادثة
CHOOSING_ACTION, CHOOSING_CATEGORY, NOTE_TITLE, NOTE_CONTENT, NOTE_PRIORITY, NOTE_REMINDER, REMINDER_TIME, REMINDER_DAY, REMINDER_HOUR, REMINDER_MINUTE_GROUP, REMINDER_MINUTE, CATEGORY_NAME, EDIT_CHOICE, EDIT_NOTE, EDIT_CATEGORY, SEARCH_RESULTS = range(16)

class NotesManager:
    """إدارة الملاحظات المتقدمة"""
    
    def __init__(self):
        self.data_file = "notes_data.json"
        self.data = self.load_data()
        self.ensure_default_categories()
    
    def load_data(self):
        """تحميل البيانات"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"notes": [], "categories": [], "next_id": 1}
        except Exception as e:
            logger.error(f"خطأ في تحميل البيانات: {e}")
            return {"notes": [], "categories": [], "next_id": 1}
    
    def save_data(self):
        """حفظ البيانات"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info("تم حفظ البيانات بنجاح")
        except Exception as e:
            logger.error(f"خطأ في حفظ البيانات: {e}")
    
    def ensure_default_categories(self):
        """إنشاء التصنيفات الافتراضية"""
        default_categories = ["عام", "مهام", "أفكار"]
        if not self.data.get("categories"):
            self.data["categories"] = default_categories
            self.save_data()
    
    def add_category(self, name):
        """إضافة تصنيف جديد"""
        if name not in self.data["categories"]:
            self.data["categories"].append(name)
            self.save_data()
            return True
        return False
    
    def add_note(self, title, content, category, priority, reminder=None):
        """إضافة ملاحظة جديدة"""
        note = {
            "id": self.data["next_id"],
            "title": title,
            "content": content,
            "category": category,
            "priority": priority,
            "reminder": reminder,
            "created_at": datetime.now().isoformat()
        }
        self.data["notes"].append(note)
        self.data["next_id"] += 1
        self.save_data()
        return note
    
    def get_notes_by_category(self, category=None):
        """الحصول على الملاحظات حسب التصنيف"""
        if category:
            return [note for note in self.data["notes"] if note["category"] == category]
        return self.data["notes"]
    
    def search_notes(self, query):
        """البحث في الملاحظات"""
        query = query.lower()
        results = []
        for note in self.data["notes"]:
            if (query in note["title"].lower() or 
                query in note["content"].lower() or 
                query in note["category"].lower()):
                results.append(note)
        return results
    
    def get_note_by_id(self, note_id):
        """الحصول على ملاحظة بواسطة المعرف"""
        for note in self.data["notes"]:
            if note["id"] == note_id:
                return note
        return None
    
    def update_note(self, note_id, **kwargs):
        """تحديث ملاحظة"""
        note = self.get_note_by_id(note_id)
        if note:
            for key, value in kwargs.items():
                if key in note:
                    note[key] = value
            self.save_data()
            return True
        return False
    
    def delete_note(self, note_id):
        """حذف ملاحظة"""
        note = self.get_note_by_id(note_id)
        if note:
            self.data["notes"].remove(note)
            self.save_data()
            return True
        return False
    
    def get_stats(self):
        """الحصول على الإحصائيات"""
        total_notes = len(self.data["notes"])
        total_categories = len(self.data["categories"])
        
        # الملاحظات الحديثة (آخر 7 أيام)
        week_ago = datetime.now() - timedelta(days=7)
        recent_notes = len([note for note in self.data["notes"] 
                           if datetime.fromisoformat(note["created_at"]) > week_ago])
        
        # توزيع الأولويات
        priorities = {"🔴 مهم جداً": 0, "🟡 مهم": 0, "🟢 عادي": 0}
        for note in self.data["notes"]:
            priorities[note["priority"]] += 1
        
        # تفصيل التصنيفات
        category_stats = {}
        for category in self.data["categories"]:
            category_stats[category] = len(self.get_notes_by_category(category))
        
        return {
            "total_notes": total_notes,
            "total_categories": total_categories,
            "recent_notes": recent_notes,
            "priorities": priorities,
            "category_stats": category_stats
        }
    
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_content = f"""نسخة احتياطية للملاحظات
تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
إجمالي الملاحظات: {len(self.data["notes"])}
إجمالي التصنيفات: {len(self.data["categories"])}

"""
        
        for category in self.data["categories"]:
            notes = self.get_notes_by_category(category)
            backup_content += f"\n📁 التصنيف: {category} ({len(notes)} ملاحظة)\n"
            backup_content += "=" * 50 + "\n"
            
            for note in notes:
                backup_content += f"""
🎯 {note['title']}
📝 {note['content']}
🔴 الأولوية: {note['priority']}
📅 تاريخ الإنشاء: {note['created_at']}
⏰ التذكير: {note.get('reminder', 'بدون تذكير')}
---
"""
        
        return backup_content, f"notes_backup_{timestamp}.txt"

# إنشاء مدير الملاحظات
notes_manager = NotesManager()

def create_main_menu():
    """إنشاء القائمة الرئيسية"""
    keyboard = [
        [InlineKeyboardButton("➕ إضافة ملاحظة/تصنيف", callback_data="add")],
        [InlineKeyboardButton("📚 عرض الملاحظات", callback_data="notes")],
        [InlineKeyboardButton("✏️ تعديل/حذف", callback_data="edit")],
        [InlineKeyboardButton("🔍 البحث", callback_data="search")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("💾 نسخة احتياطية", callback_data="backup")],
        [InlineKeyboardButton("📋 القائمة الكاملة", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_priority_keyboard():
    """إنشاء لوحة مفاتيح الأولويات"""
    keyboard = [
        [InlineKeyboardButton("🔴 مهم جداً", callback_data="priority_high")],
        [InlineKeyboardButton("🟡 مهم", callback_data="priority_medium")],
        [InlineKeyboardButton("🟢 عادي", callback_data="priority_low")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_reminder_keyboard():
    """إنشاء لوحة مفاتيح التذكيرات"""
    keyboard = [
        [InlineKeyboardButton("⏰ بعد 30 دقيقة", callback_data="reminder_30min")],
        [InlineKeyboardButton("⏰ بعد ساعة", callback_data="reminder_1hour")],
        [InlineKeyboardButton("⏰ بعد ساعتين", callback_data="reminder_2hours")],
        [InlineKeyboardButton("⏰ بعد 6 ساعات", callback_data="reminder_6hours")],
        [InlineKeyboardButton("📅 غداً 9 صباحاً", callback_data="reminder_tomorrow_9am")],
        [InlineKeyboardButton("📅 غداً 6 مساءً", callback_data="reminder_tomorrow_6pm")],
        [InlineKeyboardButton("⏰ وقت مخصص", callback_data="reminder_custom")],
        [InlineKeyboardButton("🚫 بدون تذكير", callback_data="reminder_none")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    welcome_text = """
🤖 **مرحباً بك في بوت تنظيم الملاحظات الذكي!**

🚀 **المميزات الرئيسية:**
• إضافة ملاحظات منظمة مع تصنيفات
• نظام أولويات ملون (🔴🟡🟢)
• تذكيرات ذكية ومخصصة
• بحث متقدم في جميع الملاحظات
• إحصائيات تفصيلية شاملة
• نسخ احتياطية تلقائية

📋 **الأوامر المتاحة:**
• `/start` - القائمة الرئيسية
• `/add` - إضافة ملاحظة/تصنيف
• `/notes` - عرض الملاحظات
• `/edit` - تعديل/حذف
• `/search` - البحث
• `/stats` - الإحصائيات
• `/backup` - نسخة احتياطية
• `/menu` - القائمة الكاملة

🎯 **ابدأ الآن:** اختر من القائمة أدناه!
    """
    
    await update.message.reply_text(
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=create_main_menu()
    )
    return ConversationHandler.END

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة النقر على الأزرار"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "add":
        await query.edit_message_text(
            "➕ **اختر ما تريد إضافته:**\n\n"
            "📝 **ملاحظة جديدة:** مع تصنيف وأولوية وتذكير\n"
            "📁 **تصنيف جديد:** لتنظيم الملاحظات",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 ملاحظة جديدة", callback_data="add_note")],
                [InlineKeyboardButton("📁 تصنيف جديد", callback_data="add_category")],
                [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
            ])
        )
        return CHOOSING_ACTION
    
    elif query.data == "add_note":
        await start_add_note(query, context)
        return CHOOSING_CATEGORY
    
    elif query.data == "add_category":
        await query.edit_message_text(
            "📁 **إضافة تصنيف جديد:**\n\n"
            "اكتب اسم التصنيف الجديد:",
            parse_mode='Markdown'
        )
        return CATEGORY_NAME
    
    elif query.data == "notes":
        await show_notes(query)
        return ConversationHandler.END
    
    elif query.data == "edit":
        await show_edit_menu(query)
        return ConversationHandler.END
    
    elif query.data == "search":
        await query.edit_message_text(
            "🔍 **البحث في الملاحظات:**\n\n"
            "اكتب كلمة البحث (في العنوان أو النص أو التصنيف):",
            parse_mode='Markdown'
        )
        return SEARCH_RESULTS
    
    elif query.data == "stats":
        await show_stats(query)
        return ConversationHandler.END
    
    elif query.data == "backup":
        await create_backup_file(query)
        return ConversationHandler.END
    
    elif query.data == "menu":
        await show_full_menu(query)
        return ConversationHandler.END
    
    elif query.data == "back_to_main":
        await query.edit_message_text(
            "🤖 **القائمة الرئيسية:**\n\nاختر من الخيارات أدناه:",
            parse_mode='Markdown',
            reply_markup=create_main_menu()
        )
        return ConversationHandler.END
    
    # معالجة اختيار التصنيف
    elif query.data.startswith("category_"):
        category = query.data.replace("category_", "")
        context.user_data["selected_category"] = category
        await query.edit_message_text(
            f"📝 **إضافة ملاحظة في تصنيف:** {category}\n\n"
            "اكتب عنوان الملاحظة:",
            parse_mode='Markdown'
        )
        return NOTE_TITLE
    
    # معالجة اختيار الأولوية
    elif query.data.startswith("priority_"):
        priority_map = {
            "priority_high": "🔴 مهم جداً",
            "priority_medium": "🟡 مهم", 
            "priority_low": "🟢 عادي"
        }
        priority = priority_map.get(query.data, "🟢 عادي")
        context.user_data["selected_priority"] = priority
        
        await query.edit_message_text(
            f"⏰ **إعداد التذكير:**\n\n"
            f"الملاحظة: {context.user_data.get('note_title', '')}\n"
            f"الأولوية: {priority}\n\n"
            "اختر نوع التذكير:",
            parse_mode='Markdown',
            reply_markup=create_reminder_keyboard()
        )
        return NOTE_REMINDER
    
    # معالجة اختيار التذكير
    elif query.data.startswith("reminder_"):
        if query.data == "reminder_none":
            await finish_add_note(query, context)
            return ConversationHandler.END
        elif query.data == "reminder_custom":
            await start_custom_reminder(query, context)
            return REMINDER_DAY
        else:
            # تذكيرات سريعة
            reminder_time = await calculate_reminder_time(query.data)
            context.user_data["reminder_time"] = reminder_time
            await finish_add_note(query, context)
            return ConversationHandler.END

async def start_add_note(query, context):
    """بدء عملية إضافة ملاحظة"""
    categories = notes_manager.data["categories"]
    
    # إنشاء أزرار التصنيفات
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(f"📁 {category}", callback_data=f"category_{category}")])
    
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="add")])
    
    await query.edit_message_text(
        "📝 **اختر تصنيف الملاحظة:**\n\n"
        "أو اختر من التصنيفات الموجودة:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_note_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة عنوان الملاحظة"""
    title = update.message.text
    context.user_data["note_title"] = title
    
    await update.message.reply_text(
        f"📝 **اكتب نص الملاحظة:**\n\n"
        f"العنوان: {title}\n\n"
        "اكتب المحتوى الكامل للملاحظة:",
        parse_mode='Markdown'
    )
    return NOTE_CONTENT

async def handle_note_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة نص الملاحظة"""
    content = update.message.text
    context.user_data["note_content"] = content
    
    await update.message.reply_text(
        f"🎯 **اختر الأولوية:**\n\n"
        f"العنوان: {context.user_data.get('note_title', '')}\n"
        f"النص: {content[:50]}{'...' if len(content) > 50 else ''}\n\n"
        "حدد مستوى الأهمية:",
        parse_mode='Markdown',
        reply_markup=create_priority_keyboard()
    )
    return NOTE_PRIORITY

async def handle_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اسم التصنيف الجديد"""
    category_name = update.message.text.strip()
    
    if len(category_name) < 2:
        await update.message.reply_text(
            "❌ **اسم التصنيف قصير جداً!**\n\n"
            "يجب أن يكون اسم التصنيف 3 أحرف على الأقل",
            parse_mode='Markdown'
        )
        return CATEGORY_NAME
    
    if category_name in notes_manager.data["categories"]:
        await update.message.reply_text(
            f"❌ **التصنيف موجود بالفعل!**\n\n"
            f"التصنيف '{category_name}' موجود في القائمة",
            parse_mode='Markdown'
        )
        return CATEGORY_NAME
    
    # إضافة التصنيف الجديد
    success = notes_manager.add_category(category_name)
    
    if success:
        await update.message.reply_text(
            f"✅ **تم إضافة التصنيف بنجاح!**\n\n"
            f"📁 التصنيف الجديد: {category_name}\n"
            f"📊 إجمالي التصنيفات: {len(notes_manager.data['categories'])}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
            ])
        )
    else:
        await update.message.reply_text(
            "❌ **خطأ في إضافة التصنيف!**\n\n"
            "يرجى المحاولة مرة أخرى",
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

async def start_custom_reminder(query, context):
    """بدء إعداد التذكير المخصص"""
    await query.edit_message_text(
        "📅 **اختر اليوم:**\n\n"
        "متى تريد التذكير؟",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("اليوم", callback_data="day_today")],
            [InlineKeyboardButton("غداً", callback_data="day_tomorrow")],
            [InlineKeyboardButton("بعد غد", callback_data="day_day_after")],
            [InlineKeyboardButton("الأسبوع القادم", callback_data="day_next_week")],
            [InlineKeyboardButton("🔙 العودة", callback_data="add_note")]
        ])
    )

async def handle_reminder_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار اليوم"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("day_"):
        day_type = query.data.replace("day_", "")
        context.user_data["selected_day"] = day_type
        
        # إنشاء أزرار الساعات (24 ساعة)
        hour_buttons = []
        for i in range(0, 24, 3):  # 3 أزرار في كل صف
            row = []
            for j in range(3):
                hour = i + j
                if hour < 24:
                    row.append(InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"hour_{hour:02d}"))
            if row:
                hour_buttons.append(row)
        
        hour_buttons.append([InlineKeyboardButton("🔙 العودة", callback_data="reminder_custom")])
        
        await query.edit_message_text(
            f"🕐 **اختر الساعة:**\n\n"
            f"اليوم: {get_day_name(day_type)}\n\n"
            "اختر الساعة المطلوبة:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(hour_buttons)
        )
        return REMINDER_HOUR

async def handle_reminder_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار الساعة"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("hour_"):
        hour = int(query.data.replace("hour_", ""))
        context.user_data["selected_hour"] = hour
        
        # إنشاء أزرار مجموعات الدقائق
        minute_groups = [
            ("00-09", "00-09"),
            ("10-19", "10-19"),
            ("20-29", "20-29"),
            ("30-39", "30-39"),
            ("40-49", "40-49"),
            ("50-59", "50-59")
        ]
        
        minute_buttons = []
        for i in range(0, len(minute_groups), 2):
            row = []
            for j in range(2):
                if i + j < len(minute_groups):
                    group_id, group_name = minute_groups[i + j]
                    row.append(InlineKeyboardButton(group_name, callback_data=f"minute_group_{group_id}"))
            if row:
                minute_buttons.append(row)
        
        minute_buttons.append([InlineKeyboardButton("🔙 العودة", callback_data=f"day_{context.user_data.get('selected_day', 'today')}")])
        
        await query.edit_message_text(
            f"⏰ **اختر مجموعة الدقائق:**\n\n"
            f"اليوم: {get_day_name(context.user_data.get('selected_day', 'today'))}\n"
            f"الساعة: {hour:02d}:00\n\n"
            "اختر مجموعة الدقائق:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(minute_buttons)
        )
        return REMINDER_MINUTE_GROUP

async def handle_reminder_minute_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار مجموعة الدقائق"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("minute_group_"):
        minute_group = query.data.replace("minute_group_", "")
        context.user_data["selected_minute_group"] = minute_group
        
        # استخراج نطاق الدقائق
        start_min, end_min = map(int, minute_group.split("-"))
        
        # إنشاء أزرار الدقائق
        minute_buttons = []
        for i in range(start_min, end_min + 1, 5):  # 5 أزرار في كل صف
            row = []
            for j in range(5):
                minute = i + j
                if minute <= end_min:
                    row.append(InlineKeyboardButton(f"{minute:02d}", callback_data=f"minute_{minute:02d}"))
            if row:
                minute_buttons.append(row)
        
        minute_buttons.append([InlineKeyboardButton("🔙 العودة", callback_data=f"hour_{context.user_data.get('selected_hour', 0):02d}")])
        
        await query.edit_message_text(
            f"⏱️ **اختر الدقيقة:**\n\n"
            f"اليوم: {get_day_name(context.user_data.get('selected_day', 'today'))}\n"
            f"الساعة: {context.user_data.get('selected_hour', 0):02d}:00\n"
            f"المجموعة: {minute_group}\n\n"
            "اختر الدقيقة المطلوبة:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(minute_buttons)
        )
        return REMINDER_MINUTE

async def handle_reminder_minute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار الدقيقة"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("minute_"):
        minute = int(query.data.replace("minute_", ""))
        
        # حساب وقت التذكير النهائي
        reminder_time = calculate_custom_reminder_time(
            context.user_data.get("selected_day", "today"),
            context.user_data.get("selected_hour", 0),
            minute
        )
        
        context.user_data["reminder_time"] = reminder_time
        
        # إنهاء إضافة الملاحظة
        await finish_add_note(query, context)
        return ConversationHandler.END

async def calculate_reminder_time(reminder_type):
    """حساب وقت التذكير"""
    now = datetime.now()
    
    if reminder_type == "reminder_30min":
        return now + timedelta(minutes=30)
    elif reminder_type == "reminder_1hour":
        return now + timedelta(hours=1)
    elif reminder_type == "reminder_2hours":
        return now + timedelta(hours=2)
    elif reminder_type == "reminder_6hours":
        return now + timedelta(hours=6)
    elif reminder_type == "reminder_tomorrow_9am":
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    elif reminder_type == "reminder_tomorrow_6pm":
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
    
    return None

async def finish_add_note(query, context):
    """إنهاء إضافة الملاحظة"""
    try:
        title = context.user_data.get("note_title")
        content = context.user_data.get("note_content")
        category = context.user_data.get("selected_category")
        priority = context.user_data.get("selected_priority")
        reminder = context.user_data.get("reminder_time")
        
        if not all([title, content, category, priority]):
            await query.edit_message_text(
                "❌ **خطأ في البيانات!**\n\n"
                "يرجى المحاولة مرة أخرى",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
                ])
            )
            return
        
        # إضافة الملاحظة
        note = notes_manager.add_note(title, content, category, priority, reminder)
        
        # رسالة النجاح
        reminder_text = "بدون تذكير"
        if reminder:
            if isinstance(reminder, datetime):
                reminder_text = reminder.strftime("%Y-%m-%d %H:%M")
            else:
                reminder_text = str(reminder)
        
        success_text = f"""✅ **تم إضافة الملاحظة بنجاح!**

🎯 **العنوان:** {title}
📝 **المحتوى:** {content[:100]}{'...' if len(content) > 100 else ''}
📁 **التصنيف:** {category}
🔴 **الأولوية:** {priority}
⏰ **التذكير:** {reminder_text}
🆔 **المعرف:** #{note['id']}

💡 **نصائح:**
• استخدم /notes لعرض جميع الملاحظات
• استخدم /search للبحث السريع
• استخدم /edit للتعديل والحذف
"""
        
        await query.edit_message_text(
            success_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ إضافة ملاحظة أخرى", callback_data="add")],
                [InlineKeyboardButton("📚 عرض الملاحظات", callback_data="notes")],
                [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
            ])
        )
        
        # مسح البيانات المؤقتة
        context.user_data.clear()
        
    except Exception as e:
        logger.error(f"خطأ في إنهاء إضافة الملاحظة: {e}")
        await query.edit_message_text(
            f"❌ **خطأ في إضافة الملاحظة:**\n{str(e)}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
            ])
        )

async def show_notes(query):
    """عرض الملاحظات"""
    notes = notes_manager.data["notes"]
    categories = notes_manager.data["categories"]
    
    if not notes:
        await query.edit_message_text(
            "📚 **لا توجد ملاحظات بعد!**\n\n"
            "💡 ابدأ بإضافة ملاحظة جديدة باستخدام زر ➕",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
            ])
        )
        return
    
    # تجميع الملاحظات حسب التصنيف
    notes_by_category = {}
    for category in categories:
        notes_by_category[category] = notes_manager.get_notes_by_category(category)
    
    text = "📚 **الملاحظات المنظمة:**\n\n"
    
    for category, category_notes in notes_by_category.items():
        if category_notes:
            text += f"📁 **{category}** ({len(category_notes)} ملاحظة):\n"
            
            # عرض أول 5 ملاحظات
            for i, note in enumerate(category_notes[:5]):
                priority_emoji = note["priority"]
                title_preview = note["title"][:30] + "..." if len(note["title"]) > 30 else note["title"]
                text += f"  {priority_emoji} {title_preview}\n"
            
            if len(category_notes) > 5:
                text += f"  ... و {len(category_notes) - 5} ملاحظة إضافية\n"
            
            text += "\n"
    
    # إضافة أزرار التنقل
    keyboard = [
        [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_stats(query):
    """عرض الإحصائيات"""
    stats = notes_manager.get_stats()
    
    text = f"""📊 **الإحصائيات الشاملة:**

📝 **إجمالي الملاحظات:** {stats['total_notes']}
📁 **إجمالي التصنيفات:** {stats['total_categories']}
🆕 **الملاحظات الحديثة (7 أيام):** {stats['recent_notes']}

🎯 **توزيع الأولويات:**
🔴 مهم جداً: {stats['priorities']['🔴 مهم جداً']}
🟡 مهم: {stats['priorities']['🟡 مهم']}
🟢 عادي: {stats['priorities']['🟢 عادي']}

📁 **تفصيل التصنيفات:**
"""
    
    for category, count in stats['category_stats'].items():
        text += f"• {category}: {count} ملاحظة\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def create_backup_file(query):
    """إنشاء ملف النسخة الاحتياطية"""
    backup_content, filename = notes_manager.create_backup()
    
    # حفظ الملف محلياً
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(backup_content)
    
    # إرسال الملف
    try:
        with open(filename, 'rb') as f:
            await query.message.reply_document(
                document=f,
                filename=filename,
                caption="💾 **تم إنشاء النسخة الاحتياطية بنجاح!**\n\n"
                        f"📁 اسم الملف: {filename}\n"
                        f"📅 تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        # حذف الملف المحلي
        os.remove(filename)
        
        await query.edit_message_text(
            "✅ **تم إنشاء النسخة الاحتياطية بنجاح!**\n\n"
            "📁 تم إرسال الملف في رسالة منفصلة",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
            ])
        )
        
    except Exception as e:
        logger.error(f"خطأ في إرسال النسخة الاحتياطية: {e}")
        await query.edit_message_text(
            f"❌ **خطأ في إنشاء النسخة الاحتياطية:**\n{str(e)}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
            ])
        )

async def show_full_menu(query):
    """عرض القائمة الكاملة"""
    menu_text = """📋 **القائمة الكاملة للأوامر:**

🚀 **/start** - القائمة الرئيسية
   عرض جميع الخيارات المتاحة

➕ **/add** - إضافة ملاحظة/تصنيف
   • إضافة ملاحظة جديدة مع تصنيف وأولوية وتذكير
   • إضافة تصنيف جديد لتنظيم الملاحظات

📚 **/notes** - عرض الملاحظات
   • عرض جميع الملاحظات منظمة حسب التصنيفات
   • عرض أول 5 ملاحظات لكل تصنيف

✏️ **/edit** - تعديل/حذف
   • تعديل الملاحظات والتصنيفات
   • حذف الملاحظات والتصنيفات

🔍 **/search** - البحث
   • بحث متقدم في العنوان والنص والتصنيف
   • عرض أول 10 نتائج مع معاينة

📊 **/stats** - الإحصائيات
   • إحصائيات شاملة للملاحظات والتصنيفات
   • توزيع الأولويات والتصنيفات

💾 **/backup** - نسخة احتياطية
   • إنشاء ملف نصي منظم يحتوي على جميع الملاحظات
   • حفظ آمن للبيانات

📋 **/menu** - هذه القائمة
   • عرض شرح مفصل لجميع الأوامر

💡 **نصائح الاستخدام:**
• استخدم التصنيفات لتنظيم الملاحظات
• حدد الأولويات حسب الأهمية
• استفد من نظام التذكيرات الذكي
• احتفظ بنسخ احتياطية دورية
"""
    
    keyboard = [
        [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        menu_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_edit_menu(query):
    """عرض قائمة التعديل"""
    categories = notes_manager.data["categories"]
    notes = notes_manager.data["notes"]
    
    if not notes:
        await query.edit_message_text(
            "✏️ **لا توجد ملاحظات للتعديل!**\n\n"
            "💡 ابدأ بإضافة ملاحظة جديدة",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
            ])
        )
        return
    
    text = "✏️ **اختر ما تريد تعديله:**\n\n"
    
    # أزرار التصنيفات
    category_buttons = []
    for category in categories:
        count = len(notes_manager.get_notes_by_category(category))
        if count > 0:
            category_buttons.append(
                InlineKeyboardButton(f"📁 {category} ({count})", callback_data=f"edit_cat_{category}")
            )
    
    # أزرار الملاحظات
    note_buttons = []
    for note in notes[:10]:  # أول 10 ملاحظات
        note_buttons.append(
            InlineKeyboardButton(f"📝 {note['title'][:20]}...", callback_data=f"edit_note_{note['id']}")
        )
    
    keyboard = []
    
    # إضافة أزرار التصنيفات
    if category_buttons:
        keyboard.append([InlineKeyboardButton("📁 تعديل التصنيفات", callback_data="edit_categories")])
        for i in range(0, len(category_buttons), 2):
            row = category_buttons[i:i+2]
            keyboard.append(row)
    
    # إضافة أزرار الملاحظات
    if note_buttons:
        keyboard.append([InlineKeyboardButton("📝 تعديل الملاحظات", callback_data="edit_notes")])
        for i in range(0, len(note_buttons), 2):
            row = note_buttons[i:i+2]
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")])
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة البحث"""
    query = update.message.text
    results = notes_manager.search_notes(query)
    
    if not results:
        await update.message.reply_text(
            f"🔍 **لا توجد نتائج للبحث:** `{query}`\n\n"
            "💡 جرب كلمات بحث أخرى أو استخدم /notes لعرض جميع الملاحظات",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
            ])
        )
        return ConversationHandler.END
    
    # عرض أول 10 نتائج
    text = f"🔍 **نتائج البحث:** `{query}`\n\n"
    text += f"📊 **عدد النتائج:** {len(results)}\n\n"
    
    for i, note in enumerate(results[:10], 1):
        priority_emoji = note["priority"]
        title_preview = note["title"][:30] + "..." if len(note["title"]) > 30 else note["title"]
        content_preview = note["content"][:50] + "..." if len(note["content"]) > 50 else note["content"]
        
        text += f"{i}. {priority_emoji} **{title_preview}**\n"
        text += f"   📝 {content_preview}\n"
        text += f"   📁 التصنيف: {note['category']} | #ID: {note['id']}\n\n"
    
    if len(results) > 10:
        text += f"... و {len(results) - 10} نتيجة إضافية\n\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
    ]
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر إضافة ملاحظة/تصنيف"""
    await start_command(update, context)

async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر عرض الملاحظات"""
    # إنشاء رسالة وهمية للاستفادة من show_notes
    class MockQuery:
        def __init__(self, message):
            self.message = message
            self.data = "notes"
        
        async def answer(self):
            pass
        
        async def edit_message_text(self, text, **kwargs):
            await self.message.reply_text(text, **kwargs)
    
    mock_query = MockQuery(update.message)
    await show_notes(mock_query)

async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر التعديل"""
    # إنشاء رسالة وهمية للاستفادة من show_edit_menu
    class MockQuery:
        def __init__(self, message):
            self.message = message
            self.data = "edit"
        
        async def answer(self):
            pass
        
        async def edit_message_text(self, text, **kwargs):
            await self.message.reply_text(text, **kwargs)
    
    mock_query = MockQuery(update.message)
    await show_edit_menu(mock_query)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البحث"""
    await update.message.reply_text(
        "🔍 **البحث في الملاحظات:**\n\n"
        "اكتب كلمة البحث (في العنوان أو النص أو التصنيف):",
        parse_mode='Markdown'
    )
    return SEARCH_RESULTS

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر الإحصائيات"""
    # إنشاء رسالة وهمية للاستفادة من show_stats
    class MockQuery:
        def __init__(self, message):
            self.message = message
            self.data = "stats"
        
        async def answer(self):
            pass
        
        async def edit_message_text(self, text, **kwargs):
            await self.message.reply_text(text, **kwargs)
    
    mock_query = MockQuery(update.message)
    await show_stats(mock_query)

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر النسخة الاحتياطية"""
    # إنشاء رسالة وهمية للاستفادة من create_backup_file
    class MockQuery:
        def __init__(self, message):
            self.message = message
            self.data = "backup"
        
        async def answer(self):
            pass
        
        async def edit_message_text(self, text, **kwargs):
            await self.message.reply_text(text, **kwargs)
    
    mock_query = MockQuery(update.message)
    await create_backup_file(mock_query)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر القائمة الكاملة"""
    # إنشاء رسالة وهمية للاستفادة من show_full_menu
    class MockQuery:
        def __init__(self, message):
            self.message = message
            self.data = "menu"
        
        async def answer(self):
            pass
        
        async def edit_message_text(self, text, **kwargs):
            await self.message.reply_text(text, **kwargs)
    
    mock_query = MockQuery(update.message)
    await show_full_menu(mock_query)

def get_day_name(day_type):
    """الحصول على اسم اليوم بالعربية"""
    day_names = {
        "today": "اليوم",
        "tomorrow": "غداً",
        "day_after": "بعد غد",
        "next_week": "الأسبوع القادم"
    }
    return day_names.get(day_type, "اليوم")

def calculate_custom_reminder_time(day_type, hour, minute):
    """حساب وقت التذكير المخصص"""
    now = datetime.now()
    
    if day_type == "today":
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_time <= now:
            target_time += timedelta(days=1)
    elif day_type == "tomorrow":
        target_time = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif day_type == "day_after":
        target_time = (now + timedelta(days=2)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif day_type == "next_week":
        target_time = (now + timedelta(days=7)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        target_time = now + timedelta(days=1)
    
    return target_time

def start_web_server():
    """خادم ويب بسيط"""
    PORT = int(os.environ.get('PORT', 8000))
    
    class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                response = f"""
                <html>
                <head><title>Notes Bot</title></head>
                <body>
                    <h1>🤖 بوت تنظيم الملاحظات يعمل!</h1>
                    <p>✅ البوت نشط ويعمل بشكل طبيعي</p>
                    <p>📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>📝 عدد الملاحظات: {len(notes_manager.data.get('notes', []))}</p>
                    <p>📁 عدد التصنيفات: {len(notes_manager.data.get('categories', []))}</p>
                    <p>🌐 الخادم: Render</p>
                </body>
                </html>
                """.encode('utf-8')
                self.wfile.write(response)
            elif self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                health_data = {
                    "status": "healthy",
                    "bot": "running",
                    "timestamp": datetime.now().isoformat(),
                    "notes_count": len(notes_manager.data.get('notes', [])),
                    "categories_count": len(notes_manager.data.get('categories', []))
                }
                self.wfile.write(json.dumps(health_data, ensure_ascii=False).encode('utf-8'))
            elif self.path == '/status':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                status_data = {
                    "bot_status": "running",
                    "notes_manager": "active",
                    "data_file": notes_manager.data_file,
                    "timestamp": datetime.now().isoformat(),
                    "stats": notes_manager.get_stats()
                }
                self.wfile.write(json.dumps(status_data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>404 - Page Not Found</h1>')
    
    try:
        with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
            logger.info(f"🌐 خادم الويب يعمل على المنفذ {PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"خطأ في خادم الويب: {e}")

def main():
    """تشغيل البوت"""
    # التأكد من التوكن
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ يرجى وضع توكن البوت الصحيح!")
        return
    
    try:
        # إنشاء التطبيق
        application = Application.builder().token(BOT_TOKEN).build()
        
        # إضافة الأوامر المباشرة
        application.add_handler(CommandHandler("add", add_command))
        application.add_handler(CommandHandler("notes", notes_command))
        application.add_handler(CommandHandler("edit", edit_command))
        application.add_handler(CommandHandler("search", search_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("backup", backup_command))
        application.add_handler(CommandHandler("menu", menu_command))
        
        # إضافة معالج المحادثة الرئيسي
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start_command),
                CallbackQueryHandler(handle_callback)
            ],
            states={
                CHOOSING_ACTION: [
                    CallbackQueryHandler(handle_callback)
                ],
                CHOOSING_CATEGORY: [
                    CallbackQueryHandler(handle_callback)
                ],
                NOTE_TITLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note_title)
                ],
                NOTE_CONTENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note_content)
                ],
                NOTE_PRIORITY: [
                    CallbackQueryHandler(handle_callback)
                ],
                NOTE_REMINDER: [
                    CallbackQueryHandler(handle_callback)
                ],
                REMINDER_DAY: [
                    CallbackQueryHandler(handle_reminder_day)
                ],
                REMINDER_HOUR: [
                    CallbackQueryHandler(handle_reminder_hour)
                ],
                REMINDER_MINUTE_GROUP: [
                    CallbackQueryHandler(handle_reminder_minute_group)
                ],
                REMINDER_MINUTE: [
                    CallbackQueryHandler(handle_reminder_minute)
                ],
                CATEGORY_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_name)
                ],
                SEARCH_RESULTS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)
                ]
            },
            fallbacks=[CommandHandler("start", start_command)]
        )
        
        application.add_handler(conv_handler)
        
        # بدء الخادم في خيط منفصل
        web_server_thread = threading.Thread(target=start_web_server, daemon=True)
        web_server_thread.start()
        
        # بدء البوت
        logger.info("🤖 بوت تنظيم الملاحظات المتقدم يعمل الآن...")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")

if __name__ == '__main__':
    main()
