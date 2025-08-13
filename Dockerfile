# Dockerfile لبوت تنظيم الملاحظات

FROM python:3.11-slim

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملفات المتطلبات
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# إنشاء مجلد للبيانات
RUN mkdir -p /app/data

# تعيين متغيرات البيئة
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# فتح المنفذ
EXPOSE 8000

# أمر التشغيل
CMD ["python", "main.py"]