#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف تشغيل بوت تنظيم الملاحظات
"""

import sys
import os

# إضافة المجلد الحالي إلى مسار Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """تشغيل البوت"""
    print("🚀 بدء تشغيل بوت تنظيم الملاحظات...")
    
    try:
        # استيراد وتشغيل البوت
        from main import main as run_bot
        run_bot()
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()