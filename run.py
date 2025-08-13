#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف تشغيل بوت تنظيم الملاحظات
"""

import os
import sys
import logging
from main import main

def setup_logging():
    """إعداد نظام التسجيل"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_requirements():
    """التحقق من المتطلبات"""
    try:
        import telegram
        import telegram.ext
        print("✅ جميع المتطلبات متوفرة")
        return True
    except ImportError as e:
        print(f"❌ خطأ في المتطلبات: {e}")
        print("💡 قم بتثبيت المتطلبات: pip install -r requirements.txt")
        return False

def check_token():
    """التحقق من توكن البوت"""
    from main import BOT_TOKEN
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ يرجى تحديث BOT_TOKEN في main.py")
        print("💡 احصل على التوكن من @BotFather")
        return False
    
    print(f"✅ توكن البوت: {BOT_TOKEN[:10]}...")
    return True

def main_setup():
    """الإعداد الرئيسي"""
    print("🤖 بوت تنظيم الملاحظات الذكي")
    print("=" * 50)
    
    # إعداد التسجيل
    setup_logging()
    
    # التحقق من المتطلبات
    if not check_requirements():
        return False
    
    # التحقق من التوكن
    if not check_token():
        return False
    
    print("🚀 بدء تشغيل البوت...")
    return True

if __name__ == "__main__":
    try:
        if main_setup():
            main()
        else:
            print("❌ فشل في الإعداد")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        logging.error(f"خطأ في التشغيل: {e}")
        sys.exit(1)