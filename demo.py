#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف تجريبي لعرض كيفية استخدام بوت تنظيم الملاحظات
"""

import sys
import os
import json
from datetime import datetime

# إضافة المجلد الحالي إلى مسار Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import NotesManager

def demo_basic_operations():
    """عرض العمليات الأساسية"""
    print("🎯 **عرض العمليات الأساسية للبوت**\n")
    
    # إنشاء مدير ملاحظات جديد
    notes_manager = NotesManager()
    
    print("1️⃣ **إضافة تصنيف جديد**")
    category_id = notes_manager.add_category("مشاريع")
    print(f"   ✅ تم إضافة تصنيف 'مشاريع' برقم #{category_id}\n")
    
    print("2️⃣ **إضافة ملاحظة جديدة**")
    note_id = notes_manager.add_note(
        title="تطوير تطبيق ويب",
        text="تطوير تطبيق ويب باستخدام React و Node.js",
        category_id=category_id,
        priority="🔴"
    )
    print(f"   ✅ تم إضافة ملاحظة برقم #{note_id}\n")
    
    print("3️⃣ **إضافة ملاحظة أخرى**")
    note_id2 = notes_manager.add_note(
        title="اجتماع فريق العمل",
        text="اجتماع أسبوعي لمناقشة تقدم المشروع",
        category_id=category_id,
        priority="🟡"
    )
    print(f"   ✅ تم إضافة ملاحظة برقم #{note_id2}\n")
    
    print("4️⃣ **إضافة ملاحظة في التصنيف الافتراضي**")
    note_id3 = notes_manager.add_note(
        title="فكرة جديدة",
        text="فكرة لتطبيق موبايل لتنظيم المهام",
        category_id=1,  # تصنيف "عام"
        priority="🟢"
    )
    print(f"   ✅ تم إضافة ملاحظة برقم #{note_id3}\n")
    
    return notes_manager

def demo_search_and_stats(notes_manager):
    """عرض البحث والإحصائيات"""
    print("🔍 **البحث والإحصائيات**\n")
    
    print("1️⃣ **البحث في الملاحظات**")
    search_results = notes_manager.search_notes("تطبيق")
    print(f"   📊 تم العثور على {len(search_results)} نتيجة للبحث في 'تطبيق'")
    for i, note in enumerate(search_results, 1):
        category_name = notes_manager.get_category_name(note["category_id"])
        print(f"   {i}. {note['priority']} {note['title']} (في {category_name})")
    print()
    
    print("2️⃣ **عرض جميع الملاحظات**")
    for category in notes_manager.data["categories"]:
        notes_in_category = notes_manager.get_notes_by_category(category["id"])
        if notes_in_category:
            print(f"   📁 {category['name']} ({len(notes_in_category)} ملاحظة):")
            for note in notes_in_category:
                print(f"      {note['priority']} {note['title']}")
            print()
    
    print("3️⃣ **الإحصائيات**")
    total_notes = len(notes_manager.data["notes"])
    total_categories = len(notes_manager.data["categories"])
    print(f"   📊 إجمالي الملاحظات: {total_notes}")
    print(f"   📁 إجمالي التصنيفات: {total_categories}")
    
    # توزيع الأولويات
    priority_counts = {"🔴": 0, "🟡": 0, "🟢": 0}
    for note in notes_manager.data["notes"]:
        priority_counts[note["priority"]] += 1
    
    print(f"   🔴 مهم جداً: {priority_counts['🔴']}")
    print(f"   🟡 مهم: {priority_counts['🟡']}")
    print(f"   🟢 عادي: {priority_counts['🟢']}")
    print()

def demo_backup(notes_manager):
    """عرض النسخ الاحتياطي"""
    print("💾 **النسخ الاحتياطي**\n")
    
    print("1️⃣ **إنشاء نسخة احتياطية**")
    backup_content, filename = notes_manager.create_backup()
    print(f"   ✅ تم إنشاء نسخة احتياطية: {filename}")
    print(f"   📏 حجم المحتوى: {len(backup_content)} حرف")
    print()
    
    print("2️⃣ **معاينة المحتوى**")
    print("   " + "="*50)
    lines = backup_content.split('\n')[:10]  # أول 10 أسطر فقط
    for line in lines:
        print(f"   {line}")
    if len(backup_content.split('\n')) > 10:
        print("   ...")
    print("   " + "="*50)
    print()

def demo_validation():
    """عرض التحقق من صحة البيانات"""
    print("✅ **التحقق من صحة البيانات**\n")
    
    from utils import is_valid_category_name, is_valid_note_title, is_valid_note_text
    
    print("1️⃣ **اختبار أسماء التصنيفات**")
    test_categories = ["تصنيف صحيح", "", "a" * 51]
    for cat in test_categories:
        is_valid = is_valid_category_name(cat)
        status = "✅ صحيح" if is_valid else "❌ غير صحيح"
        print(f"   '{cat}': {status}")
    print()
    
    print("2️⃣ **اختبار عناوين الملاحظات**")
    test_titles = ["عنوان صحيح", "", "a" * 101]
    for title in test_titles:
        is_valid = is_valid_note_title(title)
        status = "✅ صحيح" if is_valid else "❌ غير صحيح"
        print(f"   '{title}': {status}")
    print()
    
    print("3️⃣ **اختبار نصوص الملاحظات**")
    test_texts = ["نص صحيح", "", "a" * 2001]
    for text in test_texts:
        is_valid = is_valid_note_text(text)
        status = "✅ صحيح" if is_valid else "❌ غير صحيح"
        print(f"   '{text}': {status}")
    print()

def main():
    """الدالة الرئيسية"""
    print("🤖 **تجريبي بوت تنظيم الملاحظات**")
    print("=" * 60)
    print()
    
    try:
        # العمليات الأساسية
        notes_manager = demo_basic_operations()
        
        # البحث والإحصائيات
        demo_search_and_stats(notes_manager)
        
        # النسخ الاحتياطي
        demo_backup(notes_manager)
        
        # التحقق من صحة البيانات
        demo_validation()
        
        print("🎉 **انتهى العرض التجريبي بنجاح!**")
        print("\n💡 **للبدء في استخدام البوت:**")
        print("   1. تأكد من تحديث BOT_TOKEN في config.py")
        print("   2. شغل البوت: python start_bot.py")
        print("   3. ابدأ باستخدام /start في تليجرام")
        
    except Exception as e:
        print(f"❌ خطأ في العرض التجريبي: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()