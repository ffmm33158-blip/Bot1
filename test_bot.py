# -*- coding: utf-8 -*-
"""
ملف اختبار بوت تنظيم الملاحظات
"""

import unittest
import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# استيراد الملفات المحلية
import config
import utils
from main import NotesManager

class TestNotesManager(unittest.TestCase):
    """اختبارات مدير الملاحظات"""
    
    def setUp(self):
        """إعداد الاختبار"""
        # إنشاء ملف بيانات مؤقت
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        # إنشاء مدير ملاحظات جديد مع الملف المؤقت
        self.notes_manager = NotesManager()
        self.notes_manager.data_file = self.temp_file.name
        self.notes_manager.data = {"notes": [], "categories": [], "reminders": [], "stats": {"total_notes": 0, "total_categories": 0}}
    
    def tearDown(self):
        """تنظيف بعد الاختبار"""
        # حذف الملف المؤقت
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_initialize_default_categories(self):
        """اختبار تهيئة التصنيفات الافتراضية"""
        self.notes_manager.initialize_default_categories()
        
        # التحقق من وجود التصنيفات الافتراضية
        self.assertEqual(len(self.notes_manager.data["categories"]), 3)
        category_names = [cat["name"] for cat in self.notes_manager.data["categories"]]
        self.assertIn("عام", category_names)
        self.assertIn("مهام", category_names)
        self.assertIn("أفكار", category_names)
    
    def test_add_category(self):
        """اختبار إضافة تصنيف جديد"""
        category_id = self.notes_manager.add_category("اختبار")
        
        self.assertEqual(category_id, 1)
        self.assertEqual(len(self.notes_manager.data["categories"]), 1)
        self.assertEqual(self.notes_manager.data["categories"][0]["name"], "اختبار")
    
    def test_add_note(self):
        """اختبار إضافة ملاحظة جديدة"""
        # إضافة تصنيف أولاً
        category_id = self.notes_manager.add_category("اختبار")
        
        # إضافة ملاحظة
        note_id = self.notes_manager.add_note(
            title="ملاحظة اختبار",
            text="نص الملاحظة",
            category_id=category_id,
            priority="🔴"
        )
        
        self.assertEqual(note_id, 1)
        self.assertEqual(len(self.notes_manager.data["notes"]), 1)
        self.assertEqual(self.notes_manager.data["notes"][0]["title"], "ملاحظة اختبار")
    
    def test_get_category_name(self):
        """اختبار الحصول على اسم التصنيف"""
        category_id = self.notes_manager.add_category("اختبار")
        category_name = self.notes_manager.get_category_name(category_id)
        
        self.assertEqual(category_name, "اختبار")
    
    def test_search_notes(self):
        """اختبار البحث في الملاحظات"""
        # إضافة تصنيف وملاحظات
        category_id = self.notes_manager.add_category("اختبار")
        self.notes_manager.add_note("ملاحظة مهمة", "نص مهم", category_id, "🔴")
        self.notes_manager.add_note("ملاحظة عادية", "نص عادي", category_id, "🟢")
        
        # البحث
        results = self.notes_manager.search_notes("مهم")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "ملاحظة مهمة")
    
    def test_create_backup(self):
        """اختبار إنشاء النسخة الاحتياطية"""
        # إضافة بيانات للاختبار
        category_id = self.notes_manager.add_category("اختبار")
        self.notes_manager.add_note("ملاحظة اختبار", "نص الاختبار", category_id, "🔴")
        
        backup_content, filename = self.notes_manager.create_backup()
        
        self.assertIn("ملاحظة اختبار", backup_content)
        self.assertIn("اختبار", backup_content)
        self.assertTrue(filename.startswith("notes_backup_"))

class TestUtils(unittest.TestCase):
    """اختبارات المساعدات"""
    
    def test_calculate_reminder_time(self):
        """اختبار حساب وقت التذكير"""
        # اختبار التذكيرات السريعة
        reminder_30min = utils.calculate_reminder_time("30min")
        self.assertIsNotNone(reminder_30min)
        
        # التحقق من أن الوقت في المستقبل
        reminder_dt = datetime.fromisoformat(reminder_30min)
        now = datetime.now()
        self.assertGreater(reminder_dt, now)
    
    def test_calculate_custom_reminder_time(self):
        """اختبار حساب وقت التذكير المخصص"""
        # اختبار غداً
        reminder_time = utils.calculate_custom_reminder_time("tomorrow", 9, 30)
        reminder_dt = datetime.fromisoformat(reminder_time)
        
        tomorrow = datetime.now() + timedelta(days=1)
        expected_time = tomorrow.replace(hour=9, minute=30, second=0, microsecond=0)
        
        self.assertEqual(reminder_dt.hour, expected_time.hour)
        self.assertEqual(reminder_dt.minute, expected_time.minute)
    
    def test_format_note_preview(self):
        """اختبار تنسيق معاينة الملاحظة"""
        # نص قصير
        short_text = "نص قصير"
        result = utils.format_note_preview(short_text, 10)
        self.assertEqual(result, short_text)
        
        # نص طويل
        long_text = "نص طويل جداً يتجاوز الحد المطلوب"
        result = utils.format_note_preview(long_text, 10)
        self.assertEqual(result, "نص طويل جد...")
    
    def test_validation_functions(self):
        """اختبار دوال التحقق من الصحة"""
        # اختبار اسم التصنيف
        self.assertTrue(utils.is_valid_category_name("تصنيف صحيح"))
        self.assertFalse(utils.is_valid_category_name(""))
        self.assertFalse(utils.is_valid_category_name("a" * 51))
        
        # اختبار عنوان الملاحظة
        self.assertTrue(utils.is_valid_note_title("عنوان صحيح"))
        self.assertFalse(utils.is_valid_note_title(""))
        self.assertFalse(utils.is_valid_note_title("a" * 101))
        
        # اختبار نص الملاحظة
        self.assertTrue(utils.is_valid_note_text("نص صحيح"))
        self.assertFalse(utils.is_valid_note_text(""))
        self.assertFalse(utils.is_valid_note_text("a" * 2001))
    
    def test_sanitize_filename(self):
        """اختبار تنظيف اسم الملف"""
        # اختبار إزالة الأحرف غير المسموحة
        dirty_name = 'file<>:"/\\|?*name'
        clean_name = utils.sanitize_filename(dirty_name)
        self.assertNotIn('<', clean_name)
        self.assertNotIn('>', clean_name)
        self.assertNotIn(':', clean_name)
        self.assertNotIn('"', clean_name)
        self.assertNotIn('/', clean_name)
        self.assertNotIn('\\', clean_name)
        self.assertNotIn('|', clean_name)
        self.assertNotIn('?', clean_name)
        self.assertNotIn('*', clean_name)
    
    def test_calculate_stats(self):
        """اختبار حساب الإحصائيات"""
        # إنشاء بيانات اختبار
        notes = [
            {"id": 1, "title": "ملاحظة 1", "priority": "🔴", "category_id": 1, "created_at": datetime.now().isoformat()},
            {"id": 2, "title": "ملاحظة 2", "priority": "🟡", "category_id": 2, "created_at": (datetime.now() - timedelta(days=10)).isoformat()},
            {"id": 3, "title": "ملاحظة 3", "priority": "🟢", "category_id": 1, "created_at": datetime.now().isoformat()}
        ]
        
        categories = [
            {"id": 1, "name": "تصنيف 1"},
            {"id": 2, "name": "تصنيف 2"}
        ]
        
        stats = utils.calculate_stats(notes, categories)
        
        self.assertEqual(stats["total_notes"], 3)
        self.assertEqual(stats["total_categories"], 2)
        self.assertEqual(stats["priority_counts"]["🔴"], 1)
        self.assertEqual(stats["priority_counts"]["🟡"], 1)
        self.assertEqual(stats["priority_counts"]["🟢"], 1)

class TestConfig(unittest.TestCase):
    """اختبارات الإعدادات"""
    
    def test_default_categories(self):
        """اختبار التصنيفات الافتراضية"""
        self.assertIn("عام", config.DEFAULT_CATEGORIES)
        self.assertIn("مهام", config.DEFAULT_CATEGORIES)
        self.assertIn("أفكار", config.DEFAULT_CATEGORIES)
        self.assertEqual(len(config.DEFAULT_CATEGORIES), 3)
    
    def test_priorities(self):
        """اختبار الأولويات"""
        self.assertIn("🔴", config.PRIORITIES)
        self.assertIn("🟡", config.PRIORITIES)
        self.assertIn("🟢", config.PRIORITIES)
        self.assertEqual(config.PRIORITIES["🔴"], "مهم جداً")
    
    def test_messages(self):
        """اختبار الرسائل"""
        self.assertIn("welcome", config.MESSAGES)
        self.assertIn("menu", config.MESSAGES)
        self.assertIn("no_notes", config.MESSAGES)
    
    def test_error_messages(self):
        """اختبار رسائل الأخطاء"""
        self.assertIn("save_note", config.ERROR_MESSAGES)
        self.assertIn("backup", config.ERROR_MESSAGES)
        self.assertIn("web_server", config.ERROR_MESSAGES)

def run_tests():
    """تشغيل جميع الاختبارات"""
    print("🧪 بدء اختبارات بوت تنظيم الملاحظات...")
    
    # إنشاء مجموعة الاختبارات
    test_suite = unittest.TestSuite()
    
    # إضافة اختبارات مدير الملاحظات
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestNotesManager))
    
    # إضافة اختبارات المساعدات
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUtils))
    
    # إضافة اختبارات الإعدادات
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestConfig))
    
    # تشغيل الاختبارات
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # عرض النتائج
    print(f"\n📊 نتائج الاختبارات:")
    print(f"✅ نجح: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ فشل: {len(result.failures)}")
    print(f"⚠️ أخطاء: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ الاختبارات الفاشلة:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print(f"\n⚠️ الاختبارات التي تحتوي على أخطاء:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)