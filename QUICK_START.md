# 🚀 دليل التشغيل السريع

## ⚡ التشغيل في 3 خطوات

### 1. إعداد البوت
```bash
# استنساخ المشروع
git clone <repository-url>
cd notes-bot

# تثبيت المتطلبات
pip install -r requirements.txt
```

### 2. الحصول على توكن البوت
1. اذهب إلى [@BotFather](https://t.me/BotFather) في تليجرام
2. اكتب `/newbot`
3. اتبع التعليمات لإنشاء بوت جديد
4. انسخ التوكن المُعطى لك

### 3. تشغيل البوت
```bash
# تحديث التوكن في main.py
# ثم تشغيل البوت
python main.py
```

## 🐳 التشغيل باستخدام Docker

### تشغيل سريع:
```bash
# بناء وتشغيل
docker-compose up -d

# عرض السجلات
docker-compose logs -f

# إيقاف
docker-compose down
```

### تشغيل منفصل:
```bash
# بناء الصورة
docker build -t notes-bot .

# تشغيل الحاوية
docker run -d -p 8000:8000 --name notes-bot notes-bot
```

## 🔧 التكوين

### المتغيرات البيئية:
```bash
# نسخ ملف البيئة
cp .env.example .env

# تعديل القيم
nano .env
```

### إعدادات مهمة:
- `BOT_TOKEN`: توكن البوت (مطلوب)
- `PORT`: منفذ الخادم (افتراضي: 8000)
- `DATA_FILE`: ملف البيانات (افتراضي: notes_data.json)

## 📱 اختبار البوت

### 1. ابحث عن بوتك في تليجرام
### 2. اكتب `/start`
### 3. اختبر الأوامر:
- `/add` - إضافة ملاحظة
- `/notes` - عرض الملاحظات
- `/search` - البحث
- `/stats` - الإحصائيات

## 🌐 الوصول للخادم

### صفحة الحالة:
- `http://localhost:8000/` - الصفحة الرئيسية
- `http://localhost:8000/health` - صحة النظام
- `http://localhost:8000/status` - حالة البوت

## 🚨 حل المشاكل الشائعة

### خطأ "ModuleNotFoundError":
```bash
pip install -r requirements.txt
```

### خطأ "Invalid token":
- تأكد من صحة التوكن
- تأكد من أن البوت لم يتم حظره

### خطأ "Port already in use":
```bash
# تغيير المنفذ في .env
PORT=8001
```

### البوت لا يستجيب:
- تأكد من أن البوت يعمل
- تحقق من السجلات: `docker-compose logs -f`

## 📊 مراقبة الأداء

### عرض السجلات:
```bash
# سجلات مباشرة
tail -f bot.log

# سجلات Docker
docker-compose logs -f
```

### فحص الحالة:
```bash
# حالة الحاوية
docker ps

# استخدام الموارد
docker stats
```

## 🔄 التحديث

### تحديث الكود:
```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

### نسخ احتياطية:
```bash
# نسخ البيانات
cp notes_data.json backup_$(date +%Y%m%d).json

# نسخ من Docker
docker cp notes-bot:/app/notes_data.json ./backup/
```

## 📞 الدعم

### المشاكل التقنية:
- تحقق من السجلات
- تأكد من إعدادات الشبكة
- تحقق من صلاحيات الملفات

### مشاكل البوت:
- تأكد من أن البوت نشط
- تحقق من التوكن
- تأكد من عدم حظر البوت

---

**🎯 البوت جاهز للاستخدام! ابدأ بإضافة ملاحظتك الأولى باستخدام `/add`**