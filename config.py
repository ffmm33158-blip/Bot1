import os
from datetime import datetime, timedelta
import pytz

# إعدادات البوت الأساسية
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
DATA_FILE = 'notes_data.json'
BACKUP_DIR = 'backups'
LOG_FILE = 'bot.log'

# إعدادات التوقيت
TIMEZONE = pytz.timezone('Asia/Riyadh')

# إعدادات العرض
MAX_NOTES_PER_PAGE = 5
MAX_SEARCH_RESULTS = 10
MAX_PREVIEW_LENGTH = 30

# إعدادات التذكيرات
REMINDER_OPTIONS = {
    '30_min': {'text': '⏰ بعد 30 دقيقة', 'delta': timedelta(minutes=30)},
    '1_hour': {'text': '⏰ بعد ساعة', 'delta': timedelta(hours=1)},
    '2_hours': {'text': '⏰ بعد ساعتين', 'delta': timedelta(hours=2)},
    '6_hours': {'text': '⏰ بعد 6 ساعات', 'delta': timedelta(hours=6)},
    'tomorrow_9am': {'text': '📅 غداً 9 صباحاً', 'time': '09:00'},
    'tomorrow_6pm': {'text': '📅 غداً 6 مساءً', 'time': '18:00'},
    'no_reminder': {'text': '🚫 بدون تذكير', 'delta': None}
}

# إعدادات الأولويات
PRIORITY_COLORS = {
    'high': {'emoji': '🔴', 'text': 'مهم جداً', 'value': 3},
    'medium': {'emoji': '🟡', 'text': 'مهم', 'value': 2},
    'low': {'emoji': '🟢', 'text': 'عادي', 'value': 1}
}

# التصنيفات الافتراضية
DEFAULT_CATEGORIES = ['عام', 'مهام', 'أفكار']

# إعدادات الويب سيرفر
WEB_PORT = int(os.getenv('PORT', 8000))
WEB_HOST = '0.0.0.0'