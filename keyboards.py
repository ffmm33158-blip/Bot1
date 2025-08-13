from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any, Optional
from config import PRIORITY_COLORS, REMINDER_OPTIONS, MAX_NOTES_PER_PAGE
from database import db

class KeyboardManager:
    """مدير الأزرار التفاعلية"""
    
    @staticmethod
    def get_main_menu_keyboard() -> InlineKeyboardMarkup:
        """قائمة الأوامر الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("➕ إضافة ملاحظة", callback_data="add_note")],
            [InlineKeyboardButton("📚 عرض الملاحظات", callback_data="view_notes"),
             InlineKeyboardButton("🔍 البحث", callback_data="search_notes")],
            [InlineKeyboardButton("✏️ تعديل", callback_data="edit_menu"),
             InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
            [InlineKeyboardButton("💾 نسخة احتياطية", callback_data="backup"),
             InlineKeyboardButton("📋 القائمة", callback_data="menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_add_type_keyboard() -> InlineKeyboardMarkup:
        """اختيار نوع الإضافة (ملاحظة أو تصنيف)"""
        keyboard = [
            [InlineKeyboardButton("📝 إضافة ملاحظة", callback_data="add_note_type")],
            [InlineKeyboardButton("📁 إضافة تصنيف", callback_data="add_category_type")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_categories_keyboard(action: str = "select", page: int = 0, 
                               include_add_new: bool = True) -> InlineKeyboardMarkup:
        """لوحة مفاتيح التصنيفات مع التنقل"""
        categories = db.get_category_names()
        keyboard = []
        
        # حساب الصفحات
        start_idx = page * MAX_NOTES_PER_PAGE
        end_idx = start_idx + MAX_NOTES_PER_PAGE
        page_categories = categories[start_idx:end_idx]
        
        # إضافة أزرار التصنيفات
        for category in page_categories:
            callback_data = f"{action}_category_{category}"
            keyboard.append([InlineKeyboardButton(f"📁 {category}", callback_data=callback_data)])
        
        # إضافة خيار إضافة تصنيف جديد
        if include_add_new and page == 0:
            keyboard.append([InlineKeyboardButton("➕ إضافة تصنيف جديد", 
                                                callback_data="add_new_category")])
        
        # أزرار التنقل
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", 
                                                  callback_data=f"{action}_categories_page_{page-1}"))
        if end_idx < len(categories):
            nav_buttons.append(InlineKeyboardButton("➡️ التالي", 
                                                  callback_data=f"{action}_categories_page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # زر الإلغاء
        keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_priority_keyboard() -> InlineKeyboardMarkup:
        """لوحة مفاتيح الأولويات"""
        keyboard = []
        for priority_key, priority_data in PRIORITY_COLORS.items():
            emoji = priority_data['emoji']
            text = priority_data['text']
            keyboard.append([InlineKeyboardButton(f"{emoji} {text}", 
                                                callback_data=f"priority_{priority_key}")])
        
        keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_reminder_keyboard() -> InlineKeyboardMarkup:
        """لوحة مفاتيح التذكيرات"""
        keyboard = []
        
        # الخيارات السريعة
        for reminder_key, reminder_data in REMINDER_OPTIONS.items():
            text = reminder_data['text']
            keyboard.append([InlineKeyboardButton(text, 
                                                callback_data=f"reminder_{reminder_key}")])
        
        # خيار الوقت المخصص
        keyboard.append([InlineKeyboardButton("🕐 وقت مخصص", 
                                            callback_data="reminder_custom")])
        keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_custom_time_day_keyboard() -> InlineKeyboardMarkup:
        """لوحة مفاتيح اختيار اليوم للوقت المخصص"""
        keyboard = [
            [InlineKeyboardButton("📅 اليوم", callback_data="day_today")],
            [InlineKeyboardButton("📅 غداً", callback_data="day_tomorrow")],
            [InlineKeyboardButton("📅 بعد غد", callback_data="day_day_after_tomorrow")],
            [InlineKeyboardButton("📅 الأسبوع القادم", callback_data="day_next_week")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_custom_time_hour_keyboard() -> InlineKeyboardMarkup:
        """لوحة مفاتيح اختيار الساعة"""
        keyboard = []
        
        # إنشاء أزرار الساعات (0-23)
        for hour in range(0, 24, 3):  # كل 3 ساعات في صف
            row = []
            for h in range(hour, min(hour + 3, 24)):
                row.append(InlineKeyboardButton(f"{h:02d}:00", 
                                              callback_data=f"hour_{h:02d}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_custom_time_minute_group_keyboard() -> InlineKeyboardMarkup:
        """لوحة مفاتيح اختيار مجموعة الدقائق"""
        keyboard = [
            [InlineKeyboardButton("00-09", callback_data="minute_group_00")],
            [InlineKeyboardButton("10-19", callback_data="minute_group_10")],
            [InlineKeyboardButton("20-29", callback_data="minute_group_20")],
            [InlineKeyboardButton("30-39", callback_data="minute_group_30")],
            [InlineKeyboardButton("40-49", callback_data="minute_group_40")],
            [InlineKeyboardButton("50-59", callback_data="minute_group_50")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_custom_time_minute_keyboard(start_minute: int) -> InlineKeyboardMarkup:
        """لوحة مفاتيح اختيار الدقيقة الدقيقة"""
        keyboard = []
        
        # إنشاء أزرار الدقائق (10 دقائق)
        for minute in range(start_minute, start_minute + 10, 5):  # كل 5 دقائق في صف
            row = []
            for m in range(minute, min(minute + 5, start_minute + 10)):
                row.append(InlineKeyboardButton(f":{m:02d}", 
                                              callback_data=f"minute_{m:02d}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_notes_keyboard(category: Optional[str] = None, page: int = 0, 
                          action: str = "view") -> InlineKeyboardMarkup:
        """لوحة مفاتيح الملاحظات مع التنقل"""
        if category:
            notes = db.get_notes_by_category(category)
        else:
            notes = db.get_notes()
        
        keyboard = []
        
        # حساب الصفحات
        start_idx = page * MAX_NOTES_PER_PAGE
        end_idx = start_idx + MAX_NOTES_PER_PAGE
        page_notes = notes[start_idx:end_idx]
        
        # إضافة أزرار الملاحظات
        for note in page_notes:
            preview = f"{note.get_priority_emoji()} {note.title[:20]}..."
            callback_data = f"{action}_note_{note.id}"
            keyboard.append([InlineKeyboardButton(preview, callback_data=callback_data)])
        
        # أزرار التنقل
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", 
                                                  callback_data=f"{action}_notes_page_{page-1}"))
        if end_idx < len(notes):
            nav_buttons.append(InlineKeyboardButton("➡️ التالي", 
                                                  callback_data=f"{action}_notes_page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # زر الرجوع
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_edit_menu_keyboard() -> InlineKeyboardMarkup:
        """قائمة التعديل الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("✏️ تعديل ملاحظة", callback_data="edit_note_menu")],
            [InlineKeyboardButton("📁 تعديل تصنيف", callback_data="edit_category_menu")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_note_edit_options_keyboard(note_id: int) -> InlineKeyboardMarkup:
        """خيارات تعديل الملاحظة"""
        keyboard = [
            [InlineKeyboardButton("✏️ تعديل العنوان", 
                                callback_data=f"edit_note_title_{note_id}")],
            [InlineKeyboardButton("📝 تعديل النص", 
                                callback_data=f"edit_note_content_{note_id}")],
            [InlineKeyboardButton("📁 تغيير التصنيف", 
                                callback_data=f"edit_note_category_{note_id}")],
            [InlineKeyboardButton("🎯 تغيير الأولوية", 
                                callback_data=f"edit_note_priority_{note_id}")],
            [InlineKeyboardButton("⏰ تعديل التذكير", 
                                callback_data=f"edit_note_reminder_{note_id}")],
            [InlineKeyboardButton("🗑️ حذف الملاحظة", 
                                callback_data=f"delete_note_{note_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="edit_note_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_category_edit_options_keyboard(category_name: str) -> InlineKeyboardMarkup:
        """خيارات تعديل التصنيف"""
        keyboard = [
            [InlineKeyboardButton("✏️ تعديل الاسم", 
                                callback_data=f"edit_category_name_{category_name}")],
            [InlineKeyboardButton("🗑️ حذف التصنيف", 
                                callback_data=f"delete_category_{category_name}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="edit_category_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_confirmation_keyboard(action: str, item_id: str) -> InlineKeyboardMarkup:
        """لوحة تأكيد العملية"""
        keyboard = [
            [InlineKeyboardButton("✅ نعم، تأكيد", 
                                callback_data=f"confirm_{action}_{item_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_cancel_keyboard() -> InlineKeyboardMarkup:
        """زر الإلغاء فقط"""
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_back_keyboard(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
        """زر الرجوع"""
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=callback_data)]]
        return InlineKeyboardMarkup(keyboard)

# إنشاء مثيل واحد من مدير الأزرار
keyboards = KeyboardManager()