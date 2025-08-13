# 🚀 دليل البدء السريع - بوت تنظيم الملاحظات الذكي

## ⚡ التشغيل السريع (5 دقائق)

### 1. إنشاء البوت في تليجرام
1. افتح تليجرام وابحث عن `@BotFather`
2. أرسل `/newbot`
3. اختر اسم للبوت (مثال: `My Notes Bot`)
4. اختر username للبوت (مثال: `my_notes_bot`)
5. احفظ التوكن الذي سيرسله لك BotFather

### 2. تحميل وتشغيل البوت

```bash
# تحميل الملفات
git clone <repository-url>
cd notes-bot

# تثبيت المكتبات
pip install -r requirements.txt

# تعيين توكن البوت
export BOT_TOKEN="YOUR_BOT_TOKEN_HERE"

# تشغيل البوت
python main.py
```

### 3. اختبار البوت
1. ابحث عن البوت في تليجرام بالـ username الذي اخترته
2. أرسل `/start`
3. إذا رأيت رسالة الترحيب مع الأزرار، فالبوت يعمل بنجاح! 🎉

## 🔧 إعداد متغيرات البيئة

### في Windows:
```cmd
set BOT_TOKEN=YOUR_BOT_TOKEN_HERE
python main.py
```

### في Linux/Mac:
```bash
export BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
python main.py
```

### باستخدام ملف .env:
```bash
# إنشاء ملف .env
echo "BOT_TOKEN=YOUR_BOT_TOKEN_HERE" > .env

# تشغيل البوت
python main.py
```

## 🌐 نشر على Render (مجاني)

### 1. رفع الكود على GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

### 2. إعداد Render
1. اذهب إلى [render.com](https://render.com) وسجل دخول
2. انقر "New" → "Web Service"
3. اربط حساب GitHub واختر المستودع
4. املأ البيانات:
   - **Name**: `notes-bot`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. في قسم "Environment Variables":
   - **Key**: `BOT_TOKEN`
   - **Value**: التوكن من BotFather
6. انقر "Create Web Service"

### 3. التحقق من التشغيل
- انتظر حتى يكتمل النشر (2-3 دقائق)
- ستحصل على رابط مثل: `https://notes-bot-abc123.onrender.com`
- افتح الرابط للتأكد من عمل البوت
- اختبر البوت في تليجرام

## 🎯 الاستخدام الأساسي

### إضافة أول ملاحظة:
1. أرسل `/add` أو اضغط "➕ إضافة ملاحظة"
2. اختر التصنيف (أو أضف جديد)
3. اكتب عنوان الملاحظة
4. اكتب نص الملاحظة  
5. اختر الأولوية (🔴🟡🟢)
6. اختر التذكير أو "بدون تذكير"

### عرض الملاحظات:
- أرسل `/notes` لعرض جميع الملاحظات
- أرسل `/search` للبحث في ملاحظة معينة

### الإحصائيات:
- أرسل `/stats` لعرض إحصائيات مفصلة

## ❓ حل المشاكل الشائعة

### البوت لا يرد:
```bash
# تحقق من التوكن
echo $BOT_TOKEN

# تحقق من السجلات
tail -f bot.log
```

### خطأ في المكتبات:
```bash
# إعادة تثبيت المكتبات
pip install --upgrade -r requirements.txt
```

### البيانات لا تحفظ:
```bash
# تحقق من الأذونات
ls -la notes_data.json

# إنشاء مجلد النسخ الاحتياطية
mkdir -p backups
```

## 📱 اختبار المميزات

### اختبار التذكيرات:
1. أضف ملاحظة مع تذكير "بعد دقيقة"
2. انتظر دقيقة واحدة
3. يجب أن تصلك رسالة تذكير

### اختبار البحث:
1. أضف عدة ملاحظات
2. استخدم `/search` وابحث عن كلمة
3. يجب أن تظهر النتائج المطابقة

### اختبار النسخ الاحتياطي:
1. أضف بعض الملاحظات
2. استخدم `/backup`
3. يجب أن تحصل على ملف .txt

## 🎉 تهانينا!

البوت الآن يعمل بنجاح! يمكنك:
- ✅ إضافة وتنظيم الملاحظات
- ✅ استخدام التذكيرات الذكية  
- ✅ البحث في الملاحظات
- ✅ عمل نسخ احتياطية
- ✅ مراقبة الإحصائيات

للمساعدة الإضافية، راجع [README.md](README.md) الكامل أو أرسل issue على GitHub.

---
**استمتع بتنظيم ملاحظاتك! 📝✨**