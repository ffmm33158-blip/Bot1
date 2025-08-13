import asyncio
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable
import logging
from config import TIMEZONE, REMINDER_OPTIONS
from database import db

class ReminderSystem:
    """نظام التذكيرات الذكي"""
    
    def __init__(self, send_reminder_callback: Optional[Callable] = None):
        self.send_reminder_callback = send_reminder_callback
        self.is_running = False
        self.check_interval = 60  # فحص كل دقيقة
        self._reminder_thread = None
    
    def set_reminder_callback(self, callback: Callable):
        """تعيين دالة إرسال التذكيرات"""
        self.send_reminder_callback = callback
    
    def start(self):
        """بدء نظام التذكيرات"""
        if not self.is_running:
            self.is_running = True
            self._reminder_thread = threading.Thread(target=self._reminder_loop, daemon=True)
            self._reminder_thread.start()
            logging.info("تم تشغيل نظام التذكيرات")
    
    def stop(self):
        """إيقاف نظام التذكيرات"""
        self.is_running = False
        if self._reminder_thread:
            self._reminder_thread.join(timeout=5)
        logging.info("تم إيقاف نظام التذكيرات")
    
    def _reminder_loop(self):
        """حلقة فحص التذكيرات"""
        while self.is_running:
            try:
                self._check_and_send_reminders()
                threading.Event().wait(self.check_interval)
            except Exception as e:
                logging.error(f"خطأ في نظام التذكيرات: {e}")
                threading.Event().wait(self.check_interval)
    
    def _check_and_send_reminders(self):
        """فحص وإرسال التذكيرات المستحقة"""
        if not self.send_reminder_callback:
            return
        
        pending_reminders = db.get_pending_reminders()
        
        for note in pending_reminders:
            try:
                # إرسال التذكير
                self.send_reminder_callback(note)
                
                # تمييز التذكير كمرسل
                db.mark_reminder_sent(note.id)
                
                logging.info(f"تم إرسال تذكير للملاحظة: {note.title}")
                
            except Exception as e:
                logging.error(f"خطأ في إرسال التذكير للملاحظة {note.id}: {e}")
    
    @staticmethod
    def calculate_reminder_time(reminder_type: str, **kwargs) -> Optional[datetime]:
        """حساب وقت التذكير"""
        now = datetime.now(TIMEZONE)
        
        if reminder_type == 'no_reminder':
            return None
        
        # التذكيرات السريعة
        if reminder_type in REMINDER_OPTIONS:
            reminder_data = REMINDER_OPTIONS[reminder_type]
            
            if 'delta' in reminder_data and reminder_data['delta']:
                return now + reminder_data['delta']
            
            elif 'time' in reminder_data:
                # للتذكيرات المحددة بوقت (مثل غداً 9 صباحاً)
                tomorrow = now + timedelta(days=1)
                time_str = reminder_data['time']
                hour, minute = map(int, time_str.split(':'))
                return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # الوقت المخصص
        elif reminder_type == 'custom':
            return ReminderSystem._calculate_custom_time(**kwargs)
        
        return None
    
    @staticmethod
    def _calculate_custom_time(day: str, hour: int, minute: int) -> datetime:
        """حساب الوقت المخصص"""
        now = datetime.now(TIMEZONE)
        target_date = now.date()
        
        # تحديد اليوم
        if day == 'today':
            target_date = now.date()
        elif day == 'tomorrow':
            target_date = now.date() + timedelta(days=1)
        elif day == 'day_after_tomorrow':
            target_date = now.date() + timedelta(days=2)
        elif day == 'next_week':
            target_date = now.date() + timedelta(days=7)
        
        # إنشاء datetime للوقت المحدد
        target_datetime = datetime.combine(target_date, datetime.min.time())
        target_datetime = target_datetime.replace(
            hour=hour, 
            minute=minute, 
            second=0, 
            microsecond=0
        )
        
        # تطبيق المنطقة الزمنية
        target_datetime = TIMEZONE.localize(target_datetime)
        
        # التأكد من أن الوقت في المستقبل
        if target_datetime <= now:
            if day == 'today':
                # إذا كان الوقت المحدد قد مضى اليوم، جعله غداً
                target_datetime = target_datetime + timedelta(days=1)
        
        return target_datetime
    
    @staticmethod
    def format_reminder_time(reminder_time: datetime) -> str:
        """تنسيق وقت التذكير للعرض"""
        if not reminder_time:
            return "بدون تذكير"
        
        now = datetime.now(TIMEZONE)
        
        # حساب الفرق الزمني
        time_diff = reminder_time - now
        
        if time_diff.days > 0:
            return f"📅 {reminder_time.strftime('%Y-%m-%d')} في {reminder_time.strftime('%H:%M')}"
        elif time_diff.total_seconds() > 3600:  # أكثر من ساعة
            hours = int(time_diff.total_seconds() // 3600)
            return f"⏰ بعد {hours} ساعة"
        elif time_diff.total_seconds() > 60:  # أكثر من دقيقة
            minutes = int(time_diff.total_seconds() // 60)
            return f"⏰ بعد {minutes} دقيقة"
        else:
            return "⏰ الآن"
    
    @staticmethod
    def get_reminder_status(note) -> str:
        """الحصول على حالة التذكير"""
        if not note.reminder_time:
            return "🚫 بدون تذكير"
        
        now = datetime.now(TIMEZONE)
        
        if note.is_reminded:
            return "✅ تم الإرسال"
        elif note.reminder_time <= now:
            return "⏰ مستحق الإرسال"
        else:
            return f"⏳ {ReminderSystem.format_reminder_time(note.reminder_time)}"

class ReminderHelper:
    """مساعد لمعالجة بيانات التذكيرات"""
    
    @staticmethod
    def parse_day_selection(callback_data: str) -> str:
        """تحليل اختيار اليوم"""
        day_mapping = {
            'day_today': 'today',
            'day_tomorrow': 'tomorrow', 
            'day_day_after_tomorrow': 'day_after_tomorrow',
            'day_next_week': 'next_week'
        }
        return day_mapping.get(callback_data, 'today')
    
    @staticmethod
    def parse_hour_selection(callback_data: str) -> int:
        """تحليل اختيار الساعة"""
        try:
            hour_str = callback_data.replace('hour_', '')
            return int(hour_str)
        except ValueError:
            return 9  # افتراضي
    
    @staticmethod
    def parse_minute_group_selection(callback_data: str) -> int:
        """تحليل اختيار مجموعة الدقائق"""
        try:
            minute_str = callback_data.replace('minute_group_', '')
            return int(minute_str)
        except ValueError:
            return 0  # افتراضي
    
    @staticmethod
    def parse_minute_selection(callback_data: str) -> int:
        """تحليل اختيار الدقيقة"""
        try:
            minute_str = callback_data.replace('minute_', '')
            return int(minute_str)
        except ValueError:
            return 0  # افتراضي
    
    @staticmethod
    def get_day_display_name(day: str) -> str:
        """الحصول على اسم اليوم للعرض"""
        day_names = {
            'today': 'اليوم',
            'tomorrow': 'غداً',
            'day_after_tomorrow': 'بعد غد',
            'next_week': 'الأسبوع القادم'
        }
        return day_names.get(day, 'اليوم')
    
    @staticmethod
    def validate_custom_time(day: str, hour: int, minute: int) -> bool:
        """التحقق من صحة الوقت المخصص"""
        # التحقق من صحة الساعة والدقيقة
        if not (0 <= hour <= 23):
            return False
        if not (0 <= minute <= 59):
            return False
        
        # التحقق من أن الوقت في المستقبل
        now = datetime.now(TIMEZONE)
        try:
            target_time = ReminderSystem._calculate_custom_time(day, hour, minute)
            return target_time > now
        except Exception:
            return False
    
    @staticmethod
    def get_quick_reminder_options() -> list:
        """الحصول على خيارات التذكير السريعة"""
        options = []
        for key, data in REMINDER_OPTIONS.items():
            options.append({
                'key': key,
                'text': data['text'],
                'callback_data': f'reminder_{key}'
            })
        return options

# إنشاء مثيل واحد من نظام التذكيرات
reminder_system = ReminderSystem()
reminder_helper = ReminderHelper()