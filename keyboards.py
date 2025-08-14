from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 إضافة ملاحظة", callback_data="add_note")],
        [InlineKeyboardButton("📋 عرض الملاحظات", callback_data="show_notes")],
        [InlineKeyboardButton("🔍 البحث", callback_data="search")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("💾 النسخ الاحتياطي", callback_data="backup")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_priority_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔴 عالي", callback_data="priority_red")],
        [InlineKeyboardButton("🟡 متوسط", callback_data="priority_yellow")],
        [InlineKeyboardButton("🟢 منخفض", callback_data="priority_green")]
    ]
    return InlineKeyboardMarkup(keyboard)
