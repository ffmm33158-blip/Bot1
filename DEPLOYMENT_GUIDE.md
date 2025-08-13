# 🚀 دليل نشر بوت تنظيم الملاحظات على Render

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
