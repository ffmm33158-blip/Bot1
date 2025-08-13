import os
import json
import logging
import http.server
import socketserver
import threading
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# استيراد الملفات المحلية
import config
import utils

# إعداد التسجيل
logging.basicConfig(
    format=config.LOGGING_CONFIG["format"],
    level=getattr(logging, config.LOGGING_CONFIG["level"])
)
logger = logging.getLogger(__name__)

# رمز البوت
BOT_TOKEN = "8078959273:AAF5Y5F1mzNDIfPOdb3GWhzary6-vKhtUWY"

# حالات المحادثة
CHOOSING_ACTION, CHOOSING_CATEGORY, ADDING_NOTE_TITLE, ADDING_NOTE_TEXT, CHOOSING_PRIORITY, CHOOSING_REMINDER_TYPE, CHOOSING_REMINDER_TIME, CHOOSING_DAY, CHOOSING_HOUR, CHOOSING_MINUTE_GROUP, CHOOSING_MINUTE, ADDING_CATEGORY_NAME, EDITING_NOTE, EDITING_CATEGORY, SEARCHING = range(15)

class NotesManager:
    """إدارة الملاحظات المتقدمة"""
    
    def __init__(self):
        self.data_file = config.DATA_FILE
        self.data = self.load_data()
        self.initialize_default_categories()
    
    def load_data(self):
        """تحميل البيانات"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"notes": [], "categories": [], "reminders": [], "stats": {"total_notes": 0, "total_categories": 0}}
        except Exception as e:
            logger.error(f"خطأ في تحميل البيانات: {e}")
            return {"notes": [], "categories": [], "reminders": [], "stats": {"total_notes": 0, "total_categories": 0}}
    
    def save_data(self):
        """حفظ البيانات"""
        try:
            # تحديث الإحصائيات
            self.data["stats"]["total_notes"] = len(self.data["notes"])
            self.data["stats"]["total_categories"] = len(self.data["categories"])
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info("تم حفظ البيانات بنجاح")
        except Exception as e:
            logger.error(f"خطأ في حفظ البيانات: {e}")
    
    def initialize_default_categories(self):
        """تهيئة التصنيفات الافتراضية"""
        if not self.data["categories"]:
            for cat in config.DEFAULT_CATEGORIES:
                self.data["categories"].append({
                    "id": len(self.data["categories"]) + 1,
                    "name": cat,
                    "created_at": datetime.now().isoformat()
                })
            self.save_data()
    
    def add_category(self, name):
        """إضافة تصنيف جديد"""
        if not utils.is_valid_category_name(name):
            raise ValueError("اسم التصنيف غير صحيح")
            
        category_id = len(self.data["categories"]) + 1
        new_category = {
            "id": category_id,
            "name": name.strip(),
            "created_at": datetime.now().isoformat()
        }
        self.data["categories"].append(new_category)
        self.save_data()
        return category_id
    
    def add_note(self, title, text, category_id, priority, reminder=None):
        """إضافة ملاحظة جديدة"""
        if not utils.is_valid_note_title(title):
            raise ValueError("عنوان الملاحظة غير صحيح")
            
        if not utils.is_valid_note_text(text):
            raise ValueError("نص الملاحظة غير صحيح")
            
        note_id = len(self.data["notes"]) + 1
        new_note = {
            "id": note_id,
            "title": title.strip(),
            "text": text.strip(),
            "category_id": category_id,
            "priority": priority,
            "reminder": reminder,
            "created_at": datetime.now().isoformat()
        }
        self.data["notes"].append(new_note)
        self.save_data()
        return note_id
    
    def get_category_name(self, category_id):
        """الحصول على اسم التصنيف"""
        for cat in self.data["categories"]:
            if cat["id"] == category_id:
                return cat["name"]
        return "غير محدد"
    
    def get_notes_by_category(self, category_id=None):
        """الحصول على الملاحظات حسب التصنيف"""
        if category_id:
            return [note for note in self.data["notes"] if note["category_id"] == category_id]
        return self.data["notes"]
    
    def search_notes(self, query):
        """البحث في الملاحظات"""
        results = []
        query_lower = query.lower()
        
        for note in self.data["notes"]:
            if (query_lower in note["title"].lower() or 
                query_lower in note["text"].lower() or
                query_lower in self.get_category_name(note["category_id"]).lower()):
                results.append(note)
        
        return results[:config.MAX_SEARCH_RESULTS]
    
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        backup_content = utils.format_backup_content(self.data["notes"], self.data["categories"])
        filename = utils.sanitize_filename(config.format_backup_filename())
        return backup_content, filename

# إنشاء مدير الملاحظات
notes_manager = NotesManager()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    await update.message.reply_text(config.MESSAGES["welcome"], parse_mode='Markdown')

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر الإضافة"""
    keyboard = [
        [InlineKeyboardButton("📝 إضافة ملاحظة", callback_data="add_note")],
        [InlineKeyboardButton("📁 إضافة تصنيف", callback_data="add_category")]
    ]
    
    await update.message.reply_text(
        "ماذا تريد إضافة؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_ACTION

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة النقر على الأزرار"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "add_note":
        await query.edit_message_text(
            "اختر التصنيف للملاحظة:",
            reply_markup=utils.get_categories_keyboard(notes_manager.data["categories"], "select")
        )
        return CHOOSING_CATEGORY
    
    elif data == "add_category":
        await query.edit_message_text(
            "اكتب اسم التصنيف الجديد:"
        )
        return ADDING_CATEGORY_NAME
    
    elif data.startswith("select_"):
        category_id = int(data.split("_")[1])
        context.user_data["selected_category"] = category_id
        await query.edit_message_text(
            "اكتب عنوان الملاحظة:"
        )
        return ADDING_NOTE_TITLE
    
    elif data == "add_new_category":
        await query.edit_message_text(
            "اكتب اسم التصنيف الجديد:"
        )
        return ADDING_CATEGORY_NAME
    
    elif data.startswith("priority_"):
        priority = data.split("_")[1]
        context.user_data["selected_priority"] = priority
        await query.edit_message_text(
            "اختر نوع التذكير:",
            reply_markup=utils.get_reminder_type_keyboard()
        )
        return CHOOSING_REMINDER_TYPE
    
    elif data.startswith("reminder_"):
        reminder_type = data.split("_")[1]
        
        if reminder_type == "none":
            context.user_data["reminder"] = None
            await save_note_and_finish(query, context)
            return ConversationHandler.END
        elif reminder_type == "custom":
            await query.edit_message_text(
                "اختر اليوم:",
                reply_markup=utils.get_custom_days_keyboard()
            )
            return CHOOSING_DAY
        else:
            # تذكيرات سريعة
            reminder_time = utils.calculate_reminder_time(reminder_type)
            context.user_data["reminder"] = reminder_time
            await save_note_and_finish(query, context)
            return ConversationHandler.END
    
    elif data.startswith("day_"):
        day_type = data.split("_")[1]
        context.user_data["selected_day"] = day_type
        await query.edit_message_text(
            "اختر الساعة (24 ساعة):",
            reply_markup=utils.get_hours_keyboard()
        )
        return CHOOSING_HOUR
    
    elif data.startswith("hour_"):
        hour = int(data.split("_")[1])
        context.user_data["selected_hour"] = hour
        await query.edit_message_text(
            "اختر مجموعة الدقائق:",
            reply_markup=utils.get_minute_groups_keyboard()
        )
        return CHOOSING_MINUTE_GROUP
    
    elif data.startswith("minute_group_"):
        minute_group = data.split("_")[1]
        context.user_data["selected_minute_group"] = minute_group
        await query.edit_message_text(
            "اختر الدقيقة:",
            reply_markup=utils.get_minutes_keyboard(minute_group)
        )
        return CHOOSING_MINUTE
    
    elif data.startswith("minute_"):
        minute = int(data.split("_")[1])
        context.user_data["selected_minute"] = minute
        
        # حساب وقت التذكير النهائي
        reminder_time = utils.calculate_custom_reminder_time(
            context.user_data["selected_day"],
            context.user_data["selected_hour"],
            minute
        )
        context.user_data["reminder"] = reminder_time
        
        await save_note_and_finish(query, context)
        return ConversationHandler.END
    
    elif data == "cancel":
        await query.edit_message_text(config.MESSAGES["operation_cancelled"])
        return ConversationHandler.END

async def save_note_and_finish(query, context):
    """حفظ الملاحظة وإنهاء العملية"""
    try:
        note_id = notes_manager.add_note(
            title=context.user_data["note_title"],
            text=context.user_data["note_text"],
            category_id=context.user_data["selected_category"],
            priority=context.user_data["selected_priority"],
            reminder=context.user_data.get("reminder")
        )
        
        category_name = notes_manager.get_category_name(context.user_data["selected_category"])
        priority_text = utils.get_priority_text(context.user_data["selected_priority"])
        reminder_text = utils.format_reminder_time(context.user_data.get("reminder"))
        
        success_text = f"""
{config.MESSAGES['note_added_success']}

🎯 **العنوان:** {context.user_data['note_title']}
📁 **التصنيف:** {category_name}
{context.user_data['selected_priority']} **الأولوية:** {priority_text}
📅 **التذكير:** {reminder_text}
🆔 **رقم الملاحظة:** #{note_id}
        """
        
        await query.edit_message_text(success_text, parse_mode='Markdown')
        
        # مسح البيانات المؤقتة
        context.user_data.clear()
        
    except Exception as e:
        logger.error(f"خطأ في حفظ الملاحظة: {e}")
        await query.edit_message_text(
            config.ERROR_MESSAGES["save_note"].format(error=str(e))
        )

async def handle_note_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة عنوان الملاحظة"""
    if not utils.is_valid_note_title(update.message.text):
        await update.message.reply_text("❌ عنوان الملاحظة غير صحيح. يجب أن يكون بين 1-100 حرف.")
        return ADDING_NOTE_TITLE
        
    context.user_data["note_title"] = update.message.text
    await update.message.reply_text("اكتب نص الملاحظة:")
    return ADDING_NOTE_TEXT

async def handle_note_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة نص الملاحظة"""
    if not utils.is_valid_note_text(update.message.text):
        await update.message.reply_text("❌ نص الملاحظة غير صحيح. يجب أن يكون بين 1-2000 حرف.")
        return ADDING_NOTE_TEXT
        
    context.user_data["note_text"] = update.message.text
    await update.message.reply_text(
        "اختر الأولوية:",
        reply_markup=utils.get_priority_keyboard()
    )
    return CHOOSING_PRIORITY

async def handle_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اسم التصنيف الجديد"""
    try:
        category_name = update.message.text
        category_id = notes_manager.add_category(category_name)
        
        await update.message.reply_text(
            config.MESSAGES["category_added_success"].format(
                name=category_name, id=category_id
            )
        )
        return ConversationHandler.END
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}")
        return ADDING_CATEGORY_NAME

async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر عرض الملاحظات"""
    if not notes_manager.data["notes"]:
        await update.message.reply_text(config.MESSAGES["no_notes"])
        return
    
    notes_text = "📚 **جميع الملاحظات:**\n\n"
    
    for category in notes_manager.data["categories"]:
        category_notes = notes_manager.get_notes_by_category(category["id"])
        if category_notes:
            notes_text += f"📁 **{category['name']}** ({len(category_notes)} ملاحظة):\n"
            
            # عرض أول 5 ملاحظات فقط
            for i, note in enumerate(category_notes[:config.MAX_NOTES_PER_CATEGORY]):
                priority_emoji = note["priority"]
                title_preview = utils.format_note_preview(note["title"], config.MAX_TITLE_PREVIEW)
                notes_text += f"  {priority_emoji} {title_preview}\n"
            
            if len(category_notes) > config.MAX_NOTES_PER_CATEGORY:
                notes_text += f"  ... و {len(category_notes) - config.MAX_NOTES_PER_CATEGORY} ملاحظة إضافية\n"
            
            notes_text += "\n"
    
    await update.message.reply_text(notes_text, parse_mode='Markdown')

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البحث"""
    await update.message.reply_text("اكتب كلمة البحث:")
    return SEARCHING

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة البحث"""
    query = update.message.text
    results = notes_manager.search_notes(query)
    
    if not results:
        await update.message.reply_text(f"🔍 لم يتم العثور على نتائج للبحث: '{query}'")
        return ConversationHandler.END
    
    search_text = f"🔍 **نتائج البحث: '{query}'**\n"
    search_text += f"📊 تم العثور على {len(results)} نتيجة:\n\n"
    
    for i, note in enumerate(results, 1):
        category_name = notes_manager.get_category_name(note["category_id"])
        priority_emoji = note["priority"]
        title_preview = utils.format_note_preview(note["title"], config.MAX_TITLE_PREVIEW)
        text_preview = utils.format_text_preview(note["text"], config.MAX_TEXT_PREVIEW)
        
        search_text += f"{i}. {priority_emoji} **{title_preview}**\n"
        search_text += f"   📝 {text_preview}\n"
        search_text += f"   📁 {category_name} | #{note['id']}\n\n"
    
    await update.message.reply_text(search_text, parse_mode='Markdown')
    return ConversationHandler.END

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر الإحصائيات"""
    stats = utils.calculate_stats(notes_manager.data["notes"], notes_manager.data["categories"])
    
    # تفصيل كل تصنيف
    category_details = []
    for category_detail in stats["category_details"]:
        category_details.append(f"  📁 {category_detail['name']}: {category_detail['count']} ملاحظة")
    
    stats_text = f"""
📊 **إحصائيات شاملة:**

📈 **الأرقام العامة:**
• إجمالي الملاحظات: {stats['total_notes']}
• إجمالي التصنيفات: {stats['total_categories']}
• الملاحظات الحديثة (7 أيام): {stats['recent_notes']}

🎯 **توزيع الأولويات:**
• 🔴 مهم جداً: {stats['priority_counts']['🔴']}
• 🟡 مهم: {stats['priority_counts']['🟡']}
• 🟢 عادي: {stats['priority_counts']['🟢']}

📁 **تفصيل التصنيفات:**
{chr(10).join(category_details)}
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر النسخ الاحتياطي"""
    try:
        backup_content, filename = notes_manager.create_backup()
        
        # حفظ الملف مؤقتاً
        temp_file_path = os.path.join(config.BACKUP_DIR, filename)
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
        
        # إرسال الملف
        with open(temp_file_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=filename,
                caption=config.MESSAGES["backup_success"]
            )
        
        # حذف الملف المؤقت
        os.remove(temp_file_path)
        
    except Exception as e:
        logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
        await update.message.reply_text(
            config.ERROR_MESSAGES["backup"].format(error=str(e))
        )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر القائمة"""
    await update.message.reply_text(config.MESSAGES["menu"], parse_mode='Markdown')

def start_web_server():
    """خادم ويب بسيط"""
    PORT = config.PORT
    HOST = config.HOST
    
    class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                # استخدام قالب HTML من config
                response = config.WEB_PAGES["main"].format(
                    timestamp=config.get_current_timestamp(),
                    notes_count=len(notes_manager.data['notes']),
                    categories_count=len(notes_manager.data['categories'])
                ).encode('utf-8')
                
                self.wfile.write(response)
            elif self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                health_data = {
                    "status": "healthy",
                    "bot": "running",
                    "timestamp": datetime.now().isoformat(),
                    "notes_count": len(notes_manager.data['notes']),
                    "categories_count": len(notes_manager.data['categories'])
                }
                self.wfile.write(json.dumps(health_data, ensure_ascii=False).encode('utf-8'))
            elif self.path == '/status':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                status_data = {
                    "bot_status": "active",
                    "notes_manager": "working",
                    "data_file": notes_manager.data_file,
                    "last_backup": "manual",
                    "uptime": "continuous"
                }
                self.wfile.write(json.dumps(status_data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>404 - Page Not Found</h1>')
    
    try:
        with socketserver.TCPServer((HOST, PORT), SimpleHTTPRequestHandler) as httpd:
            logger.info(f"🌐 خادم الويب يعمل على {HOST}:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(config.ERROR_MESSAGES["web_server"].format(error=e))

def main():
    """تشغيل البوت"""
    # التأكد من التوكن
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(config.ERROR_MESSAGES["invalid_token"])
        return
    
    try:
        # إنشاء التطبيق
        application = Application.builder().token(BOT_TOKEN).build()
        
        # إضافة الأوامر
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CommandHandler("notes", notes_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("backup", backup_command))
        
        # إضافة معالج الإضافة
        add_handler = ConversationHandler(
            entry_points=[CommandHandler("add", add_command)],
            states={
                CHOOSING_ACTION: [CallbackQueryHandler(button_callback)],
                CHOOSING_CATEGORY: [CallbackQueryHandler(button_callback)],
                ADDING_NOTE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note_title)],
                ADDING_NOTE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note_text)],
                CHOOSING_PRIORITY: [CallbackQueryHandler(button_callback)],
                CHOOSING_REMINDER_TYPE: [CallbackQueryHandler(button_callback)],
                CHOOSING_DAY: [CallbackQueryHandler(button_callback)],
                CHOOSING_HOUR: [CallbackQueryHandler(button_callback)],
                CHOOSING_MINUTE_GROUP: [CallbackQueryHandler(button_callback)],
                CHOOSING_MINUTE: [CallbackQueryHandler(button_callback)],
                ADDING_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_name)]
            },
            fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
        )
        application.add_handler(add_handler)
        
        # إضافة معالج البحث
        search_handler = ConversationHandler(
            entry_points=[CommandHandler("search", search_command)],
            states={
                SEARCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)]
            },
            fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
        )
        application.add_handler(search_handler)
        
        # بدء الخادم في خيط منفصل
        web_server_thread = threading.Thread(target=start_web_server, daemon=True)
        web_server_thread.start()
        
        # بدء البوت
        logger.info("🤖 بوت تنظيم الملاحظات المتقدم يعمل الآن...")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(config.ERROR_MESSAGES["bot_start"].format(error=e))

if __name__ == '__main__':
    main()
