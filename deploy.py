# -*- coding: utf-8 -*-
"""
ملف نشر بوت تنظيم الملاحظات على Render
"""

import os
import subprocess
import sys
import json
from datetime import datetime

def check_requirements():
    """التحقق من المتطلبات الأساسية"""
    print("🔍 التحقق من المتطلبات...")
    
    # التحقق من وجود Python
    try:
        python_version = subprocess.check_output(['python', '--version'], stderr=subprocess.STDOUT, text=True)
        print(f"✅ Python: {python_version.strip()}")
    except:
        try:
            python_version = subprocess.check_output(['python3', '--version'], stderr=subprocess.STDOUT, text=True)
            print(f"✅ Python3: {python_version.strip()}")
        except:
            print("❌ Python غير مثبت")
            return False
    
    # التحقق من وجود pip
    try:
        pip_version = subprocess.check_output(['pip', '--version'], stderr=subprocess.STDOUT, text=True)
        print(f"✅ pip: {pip_version.strip()}")
    except:
        try:
            pip_version = subprocess.check_output(['pip3', '--version'], stderr=subprocess.STDOUT, text=True)
            print(f"✅ pip3: {pip_version.strip()}")
        except:
            print("❌ pip غير مثبت")
            return False
    
    return True

def install_dependencies():
    """تثبيت المكتبات المطلوبة"""
    print("\n📦 تثبيت المكتبات المطلوبة...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ تم تثبيت جميع المكتبات بنجاح")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تثبيت المكتبات: {e}")
        return False

def run_tests():
    """تشغيل الاختبارات"""
    print("\n🧪 تشغيل الاختبارات...")
    
    try:
        result = subprocess.run([sys.executable, 'test_bot.py'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ جميع الاختبارات نجحت")
            return True
        else:
            print("❌ بعض الاختبارات فشلت")
            print("الخطأ:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ خطأ في تشغيل الاختبارات: {e}")
        return False

def check_config():
    """التحقق من الإعدادات"""
    print("\n⚙️ التحقق من الإعدادات...")
    
    try:
        import config
        
        # التحقق من التوكن
        if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("⚠️ تحذير: يجب تحديث توكن البوت في ملف config.py")
            return False
        
        print("✅ تم العثور على توكن البوت")
        
        # التحقق من الملفات المطلوبة
        required_files = ['main.py', 'config.py', 'utils.py', 'requirements.txt']
        for file in required_files:
            if os.path.exists(file):
                print(f"✅ {file}")
            else:
                print(f"❌ {file} غير موجود")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ خطأ في استيراد config: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ في التحقق من الإعدادات: {e}")
        return False

def create_render_files():
    """إنشاء ملفات Render المطلوبة"""
    print("\n🌐 إنشاء ملفات Render...")
    
    # إنشاء Dockerfile
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
"""
    
    try:
        with open('Dockerfile', 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        print("✅ تم إنشاء Dockerfile")
    except Exception as e:
        print(f"❌ خطأ في إنشاء Dockerfile: {e}")
        return False
    
    # إنشاء .dockerignore
    dockerignore_content = """__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
notes_data.json
notes_backup_*.txt
"""
    
    try:
        with open('.dockerignore', 'w', encoding='utf-8') as f:
            f.write(dockerignore_content)
        print("✅ تم إنشاء .dockerignore")
    except Exception as e:
        print(f"❌ خطأ في إنشاء .dockerignore: {e}")
        return False
    
    # إنشاء docker-compose.yml
    docker_compose_content = """version: '3.8'

services:
  notes-bot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
    volumes:
      - ./notes_data.json:/app/notes_data.json
    restart: unless-stopped
"""
    
    try:
        with open('docker-compose.yml', 'w', encoding='utf-8') as f:
            f.write(docker_compose_content)
        print("✅ تم إنشاء docker-compose.yml")
    except Exception as e:
        print(f"❌ خطأ في إنشاء docker-compose.yml: {e}")
        return False
    
    return True

def create_deployment_guide():
    """إنشاء دليل النشر"""
    print("\n📚 إنشاء دليل النشر...")
    
    guide_content = """# 🚀 دليل نشر بوت تنظيم الملاحظات على Render

## 📋 المتطلبات الأساسية

1. حساب على [Render](https://render.com)
2. توكن بوت تليجرام صحيح
3. معرفة أساسية بـ Git

## 🔧 خطوات النشر

### 1. إعداد البوت

1. تأكد من تحديث `BOT_TOKEN` في ملف `config.py`
2. تأكد من تثبيت جميع المكتبات: `pip install -r requirements.txt`
3. اختبر البوت محلياً: `python test_bot.py`

### 2. رفع الكود إلى GitHub

```bash
git init
git add .
git commit -m "إضافة بوت تنظيم الملاحظات"
git branch -M main
git remote add origin <رابط_المستودع>
git push -u origin main
```

### 3. النشر على Render

1. اذهب إلى [Render Dashboard](https://dashboard.render.com)
2. انقر على "New +" ثم اختر "Web Service"
3. اربط المستودع من GitHub
4. أدخل المعلومات التالية:
   - **Name**: notes-bot
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Port**: 8000

### 4. إعداد المتغيرات البيئية

أضف المتغيرات التالية في Render:
- `BOT_TOKEN`: توكن البوت الخاص بك
- `PORT`: 8000

### 5. النشر

انقر على "Create Web Service" وانتظر اكتمال النشر.

## 🌐 اختبار البوت

بعد النشر، يمكنك اختبار:
- الصفحة الرئيسية: `https://your-app-name.onrender.com`
- صفحة الصحة: `https://your-app-name.onrender.com/health`
- صفحة الحالة: `https://your-app-name.onrender.com/status`

## 🔍 استكشاف الأخطاء

### مشاكل شائعة:

1. **البوت لا يستجيب**: تحقق من صحة التوكن
2. **خطأ في المكتبات**: تأكد من `requirements.txt`
3. **خطأ في المنفذ**: تأكد من تعيين PORT=8000

### سجلات الأخطاء:

في Render Dashboard، اذهب إلى "Logs" لرؤية سجلات الأخطاء.

## 📞 الدعم

إذا واجهت مشاكل:
1. تحقق من سجلات Render
2. تأكد من صحة التوكن
3. اختبر البوت محلياً أولاً

---

**🎉 تهانينا! بوتك يعمل الآن على Render! 🚀**
"""
    
    try:
        with open('DEPLOYMENT_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print("✅ تم إنشاء دليل النشر")
    except Exception as e:
        print(f"❌ خطأ في إنشاء دليل النشر: {e}")
        return False
    
    return True

def main():
    """الدالة الرئيسية"""
    print("🚀 بدء عملية نشر بوت تنظيم الملاحظات...")
    print("=" * 50)
    
    # التحقق من المتطلبات
    if not check_requirements():
        print("\n❌ فشل في التحقق من المتطلبات")
        return False
    
    # التحقق من الإعدادات
    if not check_config():
        print("\n❌ فشل في التحقق من الإعدادات")
        return False
    
    # تثبيت المكتبات
    if not install_dependencies():
        print("\n❌ فشل في تثبيت المكتبات")
        return False
    
    # تشغيل الاختبارات
    if not run_tests():
        print("\n❌ فشل في الاختبارات")
        return False
    
    # إنشاء ملفات Render
    if not create_render_files():
        print("\n❌ فشل في إنشاء ملفات Render")
        return False
    
    # إنشاء دليل النشر
    if not create_deployment_guide():
        print("\n❌ فشل في إنشاء دليل النشر")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 تم إعداد البوت للنشر بنجاح!")
    print("\n📋 الخطوات التالية:")
    print("1. رفع الكود إلى GitHub")
    print("2. النشر على Render")
    print("3. اختبار البوت")
    print("\n📚 راجع DEPLOYMENT_GUIDE.md للحصول على تعليمات مفصلة")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)