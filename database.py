import json
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
from models import Note, Category, UserSession
from config import DATA_FILE, BACKUP_DIR, DEFAULT_CATEGORIES, TIMEZONE, MAX_SEARCH_RESULTS

class DatabaseManager:
    """مدير قاعدة البيانات للملاحظات"""
    
    def __init__(self):
        self.data_file = DATA_FILE
        self.backup_dir = BACKUP_DIR
        self.user_sessions: Dict[int, UserSession] = {}
        self._ensure_directories()
        self._load_data()
    
    def _ensure_directories(self):
        """التأكد من وجود المجلدات المطلوبة"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def _load_data(self):
        """تحميل البيانات من الملف"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.notes = [Note.from_dict(note_data) for note_data in data.get('notes', [])]
                    self.categories = [Category.from_dict(cat_data) for cat_data in data.get('categories', [])]
            else:
                self._initialize_default_data()
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"خطأ في تحميل البيانات: {e}")
            self._initialize_default_data()
    
    def _initialize_default_data(self):
        """تهيئة البيانات الافتراضية"""
        self.notes = []
        self.categories = [Category(name) for name in DEFAULT_CATEGORIES]
        self._save_data()
    
    def _save_data(self):
        """حفظ البيانات في الملف"""
        try:
            # إنشاء نسخة احتياطية قبل الحفظ
            self._create_backup()
            
            data = {
                'notes': [note.to_dict() for note in self.notes],
                'categories': [cat.to_dict() for cat in self.categories],
                'last_updated': datetime.now(TIMEZONE).isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logging.info("تم حفظ البيانات بنجاح")
        except Exception as e:
            logging.error(f"خطأ في حفظ البيانات: {e}")
            raise
    
    def _create_backup(self):
        """إنشاء نسخة احتياطية"""
        if os.path.exists(self.data_file):
            timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.json")
            shutil.copy2(self.data_file, backup_file)
            
            # حذف النسخ الاحتياطية القديمة (الاحتفاظ بـ 10 نسخ فقط)
            self._cleanup_old_backups()
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith('backup_')]
            backup_files.sort(reverse=True)
            
            for old_backup in backup_files[keep_count:]:
                os.remove(os.path.join(self.backup_dir, old_backup))
        except Exception as e:
            logging.warning(f"خطأ في تنظيف النسخ الاحتياطية: {e}")
    
    # إدارة الجلسات
    def get_user_session(self, user_id: int) -> UserSession:
        """الحصول على جلسة المستخدم"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(user_id)
        return self.user_sessions[user_id]
    
    def clear_user_session(self, user_id: int):
        """مسح جلسة المستخدم"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id].reset()
    
    # إدارة التصنيفات
    def get_categories(self) -> List[Category]:
        """الحصول على جميع التصنيفات"""
        return self.categories
    
    def get_category_names(self) -> List[str]:
        """الحصول على أسماء التصنيفات"""
        return [cat.name for cat in self.categories]
    
    def add_category(self, name: str) -> bool:
        """إضافة تصنيف جديد"""
        if name not in self.get_category_names():
            self.categories.append(Category(name))
            self._save_data()
            return True
        return False
    
    def update_category(self, old_name: str, new_name: str) -> bool:
        """تحديث اسم تصنيف"""
        if new_name in self.get_category_names():
            return False
        
        # تحديث اسم التصنيف
        for category in self.categories:
            if category.name == old_name:
                category.name = new_name
                break
        
        # تحديث الملاحظات التي تستخدم هذا التصنيف
        for note in self.notes:
            if note.category == old_name:
                note.category = new_name
        
        self._save_data()
        return True
    
    def delete_category(self, name: str) -> bool:
        """حذف تصنيف ونقل الملاحظات إلى 'عام'"""
        if name == 'عام':  # لا يمكن حذف التصنيف الأساسي
            return False
        
        # نقل الملاحظات إلى التصنيف العام
        for note in self.notes:
            if note.category == name:
                note.category = 'عام'
        
        # حذف التصنيف
        self.categories = [cat for cat in self.categories if cat.name != name]
        self._save_data()
        return True
    
    # إدارة الملاحظات
    def get_notes(self) -> List[Note]:
        """الحصول على جميع الملاحظات"""
        return sorted(self.notes, key=lambda x: x.created_at, reverse=True)
    
    def get_notes_by_category(self, category: str) -> List[Note]:
        """الحصول على الملاحظات حسب التصنيف"""
        return [note for note in self.get_notes() if note.category == category]
    
    def get_note_by_id(self, note_id: int) -> Optional[Note]:
        """الحصول على ملاحظة بالمعرف"""
        for note in self.notes:
            if note.id == note_id:
                return note
        return None
    
    def add_note(self, title: str, content: str, category: str, priority: str = 'low', 
                 reminder_time: Optional[datetime] = None) -> Note:
        """إضافة ملاحظة جديدة"""
        note = Note(title, content, category, priority, reminder_time=reminder_time)
        self.notes.append(note)
        self._save_data()
        return note
    
    def update_note(self, note_id: int, **kwargs) -> bool:
        """تحديث ملاحظة"""
        note = self.get_note_by_id(note_id)
        if note:
            for key, value in kwargs.items():
                if hasattr(note, key):
                    setattr(note, key, value)
            self._save_data()
            return True
        return False
    
    def delete_note(self, note_id: int) -> bool:
        """حذف ملاحظة"""
        initial_count = len(self.notes)
        self.notes = [note for note in self.notes if note.id != note_id]
        if len(self.notes) < initial_count:
            self._save_data()
            return True
        return False
    
    def search_notes(self, query: str) -> List[Note]:
        """البحث في الملاحظات"""
        query = query.lower().strip()
        if not query:
            return []
        
        results = []
        for note in self.notes:
            if (query in note.title.lower() or 
                query in note.content.lower() or 
                query in note.category.lower()):
                results.append(note)
        
        return sorted(results, key=lambda x: x.created_at, reverse=True)[:MAX_SEARCH_RESULTS]
    
    # إحصائيات
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على الإحصائيات"""
        total_notes = len(self.notes)
        total_categories = len(self.categories)
        
        # الملاحظات الحديثة (آخر 7 أيام)
        week_ago = datetime.now(TIMEZONE) - timedelta(days=7)
        recent_notes = len([note for note in self.notes if note.created_at >= week_ago])
        
        # إحصائيات التصنيفات
        category_stats = {}
        for category in self.get_category_names():
            category_stats[category] = len(self.get_notes_by_category(category))
        
        # إحصائيات الأولويات
        priority_stats = {'high': 0, 'medium': 0, 'low': 0}
        for note in self.notes:
            if note.priority in priority_stats:
                priority_stats[note.priority] += 1
        
        return {
            'total_notes': total_notes,
            'total_categories': total_categories,
            'recent_notes': recent_notes,
            'category_stats': category_stats,
            'priority_stats': priority_stats
        }
    
    def create_backup_file(self) -> str:
        """إنشاء ملف نسخة احتياطية للتصدير"""
        timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"notes_backup_{timestamp}.txt"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(f"📝 نسخة احتياطية من الملاحظات\n")
            f.write(f"📅 تاريخ الإنشاء: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"📊 إجمالي الملاحظات: {len(self.notes)}\n")
            f.write("=" * 50 + "\n\n")
            
            # تجميع الملاحظات حسب التصنيف
            for category_name in self.get_category_names():
                category_notes = self.get_notes_by_category(category_name)
                if category_notes:
                    f.write(f"📁 {category_name} ({len(category_notes)} ملاحظات)\n")
                    f.write("-" * 30 + "\n")
                    
                    for note in category_notes:
                        f.write(f"\n{note.get_priority_emoji()} {note.title}\n")
                        f.write(f"📝 المحتوى: {note.content}\n")
                        f.write(f"📅 تاريخ الإنشاء: {note.created_at.strftime('%Y-%m-%d %H:%M')}\n")
                        if note.reminder_time:
                            f.write(f"⏰ التذكير: {note.reminder_time.strftime('%Y-%m-%d %H:%M')}\n")
                        f.write("-" * 20 + "\n")
                    
                    f.write("\n")
        
        return backup_path
    
    def get_pending_reminders(self) -> List[Note]:
        """الحصول على التذكيرات المستحقة"""
        now = datetime.now(TIMEZONE)
        pending_reminders = []
        
        for note in self.notes:
            if (note.reminder_time and 
                not note.is_reminded and 
                note.reminder_time <= now):
                pending_reminders.append(note)
        
        return pending_reminders
    
    def mark_reminder_sent(self, note_id: int):
        """تمييز التذكير كمرسل"""
        note = self.get_note_by_id(note_id)
        if note:
            note.is_reminded = True
            self._save_data()

# إنشاء مثيل واحد من مدير قاعدة البيانات
db = DatabaseManager()