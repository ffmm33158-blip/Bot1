# -*- coding: utf-8 -*-
"""
ملف المساعدات والوظائف المشتركة
"""

from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config

def get_priority_keyboard():
    """لوحة مفاتيح الأولويات"""
    keyboard = [
        [InlineKeyboardButton("🔴 مهم جداً", callback_data="priority_🔴")],
        [InlineKeyboardButton("🟡 مهم", callback_data="priority_🟡")],
        [InlineKeyboardButton("🟢 عادي", callback_data="priority_🟢")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reminder_type_keyboard():
    """لوحة مفاتيح نوع التذكير"""
    keyboard = [
        [InlineKeyboardButton("⏰ بعد 30 دقيقة", callback_data="reminder_30min")],
        [InlineKeyboardButton("⏰ بعد ساعة", callback_data="reminder_1hour")],
        [InlineKeyboardButton("⏰ بعد ساعتين", callback_data="reminder_2hours")],
        [InlineKeyboardButton("⏰ بعد 6 ساعات", callback_data="reminder_6hours")],
        [InlineKeyboardButton("📅 غداً 9 صباحاً", callback_data="reminder_tomorrow_9am")],
        [InlineKeyboardButton("📅 غداً 6 مساءً", callback_data="reminder_tomorrow_6pm")],
        [InlineKeyboardButton("🚫 بدون تذكير", callback_data="reminder_none")],
        [InlineKeyboardButton("⏰ وقت مخصص", callback_data="reminder_custom")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_categories_keyboard(categories, action="select"):
    """لوحة مفاتيح التصنيفات"""
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(
            f"📁 {category['name']}", 
            callback_data=f"{action}_{category['id']}"
        )])
    
    if action == "select":
        keyboard.append([InlineKeyboardButton("➕ إضافة تصنيف جديد", callback_data="add_new_category")])
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

def get_hours_keyboard():
    """لوحة مفاتيح الساعات"""
    keyboard = []
    row = []
    for hour in range(24):
        row.append(InlineKeyboardButton(f"{hour:02d}", callback_data=f"hour_{hour}"))
        if len(row) == 6:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

def get_minute_groups_keyboard():
    """لوحة مفاتيح مجموعات الدقائق"""
    keyboard = [
        [InlineKeyboardButton("00-09", callback_data="minute_group_00-09")],
        [InlineKeyboardButton("10-19", callback_data="minute_group_10-19")],
        [InlineKeyboardButton("20-29", callback_data="minute_group_20-29")],
        [InlineKeyboardButton("30-39", callback_data="minute_group_30-39")],
        [InlineKeyboardButton("40-49", callback_data="minute_group_40-49")],
        [InlineKeyboardButton("50-59", callback_data="minute_group_50-59")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_minutes_keyboard(minute_group):
    """لوحة مفاتيح الدقائق"""
    start, end = map(int, minute_group.split("-"))
    keyboard = []
    row = []
    for minute in range(start, end + 1):
        row.append(InlineKeyboardButton(f"{minute:02d}", callback_data=f"minute_{minute}"))
        if len(row) == 6:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

def get_custom_days_keyboard():
    """لوحة مفاتيح الأيام المخصصة"""
    keyboard = [
        [InlineKeyboardButton("اليوم", callback_data="day_today")],
        [InlineKeyboardButton("غداً", callback_data="day_tomorrow")],
        [InlineKeyboardButton("بعد غد", callback_data="day_day_after")],
        [InlineKeyboardButton("الأسبوع القادم", callback_data="day_next_week")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def calculate_reminder_time(reminder_type):
    """حساب وقت التذكير للتذكيرات السريعة"""
    now = datetime.now()
    
    if reminder_type == "30min":
        return (now + timedelta(minutes=30)).isoformat()
    elif reminder_type == "1hour":
        return (now + timedelta(hours=1)).isoformat()
    elif reminder_type == "2hours":
        return (now + timedelta(hours=2)).isoformat()
    elif reminder_type == "6hours":
        return (now + timedelta(hours=6)).isoformat()
    elif reminder_type == "tomorrow_9am":
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    elif reminder_type == "tomorrow_6pm":
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=18, minute=0, second=0, microsecond=0).isoformat()
    
    return None

def calculate_custom_reminder_time(day_type, hour, minute):
    """حساب وقت التذكير المخصص"""
    now = datetime.now()
    
    if day_type == "today":
        target_date = now
    elif day_type == "tomorrow":
        target_date = now + timedelta(days=1)
    elif day_type == "day_after":
        target_date = now + timedelta(days=2)
    elif day_type == "next_week":
        target_date = now + timedelta(days=7)
    
    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()

def format_note_preview(title, max_length=30):
    """تنسيق معاينة العنوان"""
    if len(title) > max_length:
        return title[:max_length] + "..."
    return title

def format_text_preview(text, max_length=50):
    """تنسيق معاينة النص"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

def get_priority_text(priority_emoji):
    """الحصول على نص الأولوية"""
    return config.PRIORITIES.get(priority_emoji, "غير محدد")

def format_reminder_time(reminder_time):
    """تنسيق وقت التذكير للعرض"""
    if not reminder_time:
        return "بدون تذكير"
    
    try:
        dt = datetime.fromisoformat(reminder_time)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return "وقت غير محدد"

def is_valid_category_name(name):
    """التحقق من صحة اسم التصنيف"""
    if not name or len(name.strip()) == 0:
        return False
    
    if len(name.strip()) > 50:
        return False
    
    return True

def is_valid_note_title(title):
    """التحقق من صحة عنوان الملاحظة"""
    if not title or len(title.strip()) == 0:
        return False
    
    if len(title.strip()) > 100:
        return False
    
    return True

def is_valid_note_text(text):
    """التحقق من صحة نص الملاحظة"""
    if not text or len(text.strip()) == 0:
        return False
    
    if len(text.strip()) > 2000:
        return False
    
    return True

def sanitize_filename(filename):
    """تنظيف اسم الملف"""
    # إزالة الأحرف غير المسموحة
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # إزالة المسافات الزائدة
    filename = filename.strip()
    
    return filename

def format_backup_content(notes, categories):
    """تنسيق محتوى النسخة الاحتياطية"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"""نسخة احتياطية من الملاحظات
تاريخ الإنشاء: {timestamp}
إجمالي الملاحظات: {len(notes)}
إجمالي التصنيفات: {len(categories)}

"""
    
    for category in categories:
        content += f"\n📁 التصنيف: {category['name']}\n"
        notes_in_category = [note for note in notes if note["category_id"] == category["id"]]
        
        if notes_in_category:
            for note in notes_in_category:
                priority_text = get_priority_text(note["priority"])
                reminder_text = format_reminder_time(note.get("reminder"))
                
                content += f"  🎯 {note['title']}\n"
                content += f"     الأولوية: {priority_text}\n"
                content += f"     النص: {note['text']}\n"
                content += f"     التذكير: {reminder_text}\n"
                content += f"     التاريخ: {note['created_at']}\n\n"
        else:
            content += "  (لا توجد ملاحظات)\n"
    
    return content

def calculate_stats(notes, categories):
    """حساب الإحصائيات"""
    total_notes = len(notes)
    total_categories = len(categories)
    
    # الملاحظات الحديثة (آخر 7 أيام)
    week_ago = datetime.now() - timedelta(days=7)
    recent_notes = sum(1 for note in notes 
                      if datetime.fromisoformat(note["created_at"]) > week_ago)
    
    # توزيع الأولويات
    priority_counts = {"🔴": 0, "🟡": 0, "🟢": 0}
    for note in notes:
        priority_counts[note["priority"]] += 1
    
    # تفصيل كل تصنيف
    category_details = []
    for category in categories:
        notes_count = len([note for note in notes if note["category_id"] == category["id"]])
        category_details.append({
            "name": category["name"],
            "count": notes_count
        })
    
    return {
        "total_notes": total_notes,
        "total_categories": total_categories,
        "recent_notes": recent_notes,
        "priority_counts": priority_counts,
        "category_details": category_details
    }