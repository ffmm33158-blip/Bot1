#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# استيراد الوحدات المحلية
from config import BOT_TOKEN, TIMEZONE, PRIORITY_COLORS, MAX_PREVIEW_LENGTH
from database import db
from models import Note
from keyboards import keyboards
from reminder_system import reminder_system, reminder_helper, ReminderSystem

# إعداد نظام السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NotesBot:
    """بوت تنظيم الملاحظات الذكي"""
    
    def __init__(self):
        self.app = None
        self.current_page = {}  # لتتبع الصفحات الحالية للمستخدمين
    
    def setup_application(self):
        """إعداد التطبيق والمعالجات"""
        self.app = Application.builder().token(BOT_TOKEN).build()
        
        # معالجات الأوامر
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("add", self.add_command))
        self.app.add_handler(CommandHandler("notes", self.notes_command))
        self.app.add_handler(CommandHandler("edit", self.edit_command))
        self.app.add_handler(CommandHandler("search", self.search_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("backup", self.backup_command))
        self.app.add_handler(CommandHandler("menu", self.menu_command))
        
        # معالج الأزرار
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # معالج الرسائل النصية
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message_handler))
        
        # إعداد نظام التذكيرات
        reminder_system.set_reminder_callback(self.send_reminder)
        
        logger.info("تم إعداد البوت بنجاح")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /start"""
        user = update.effective_user
        welcome_message = f"""
🤖 مرحباً {user.first_name}! أهلاً بك في بوت تنظيم الملاحظات الذكي

🌟 **مميزات البوت:**
• 📝 إضافة وتنظيم الملاحظات بتصنيفات مخصصة
• 🎯 نظام أولويات ملون (🔴 مهم جداً، 🟡 مهم، 🟢 عادي)
• ⏰ تذكيرات ذكية مع خيارات متقدمة
• 🔍 بحث سريع وفعال
• 📊 إحصائيات تفصيلية
• 💾 نسخ احتياطية آمنة

🚀 **الأوامر المتاحة:**
• /add - إضافة ملاحظة أو تصنيف جديد
• /notes - عرض جميع الملاحظات
• /edit - تعديل الملاحظات والتصنيفات
• /search - البحث في الملاحظات
• /stats - عرض الإحصائيات
• /backup - إنشاء نسخة احتياطية
• /menu - عرض هذه القائمة

💡 **نصائح الاستخدام:**
- استخدم الأزرار التفاعلية للتنقل السهل
- يمكنك إضافة تصنيفات مخصصة حسب احتياجاتك
- استفد من نظام التذكيرات لعدم نسيان المهام المهمة

اختر من القائمة أدناه للبدء:
        """
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=keyboards.get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /add"""
        await update.message.reply_text(
            "➕ **إضافة جديدة**\n\nماذا تريد أن تضيف؟",
            reply_markup=keyboards.get_add_type_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def notes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /notes"""
        await self.show_all_notes(update, context)
    
    async def edit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /edit"""
        await update.message.reply_text(
            "✏️ **قائمة التعديل**\n\nاختر ما تريد تعديله:",
            reply_markup=keyboards.get_edit_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /search"""
        session = db.get_user_session(update.effective_user.id)
        session.set_action('search')
        
        await update.message.reply_text(
            "🔍 **البحث في الملاحظات**\n\nاكتب كلمة أو جملة للبحث عنها:",
            reply_markup=keyboards.get_cancel_keyboard()
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /stats"""
        await self.show_statistics(update, context)
    
    async def backup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /backup"""
        await self.create_backup(update, context)
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /menu"""
        menu_text = """
📋 **قائمة الأوامر الكاملة**

🚀 **/start** - تنشيط البوت وعرض الترحيب
➕ **/add** - إضافة ملاحظة أو تصنيف جديد
📚 **/notes** - عرض جميع الملاحظات منظمة
✏️ **/edit** - تعديل أو حذف الملاحظات والتصنيفات
🔍 **/search** - البحث في الملاحظات
📊 **/stats** - عرض الإحصائيات التفصيلية
💾 **/backup** - إنشاء نسخة احتياطية
📋 **/menu** - عرض هذه القائمة

💡 **نصائح:**
- استخدم الأزرار للتنقل السريع
- يمكنك إلغاء أي عملية بالضغط على "إلغاء"
- البوت يحفظ بياناتك تلقائياً مع كل تغيير
        """
        
        await update.message.reply_text(
            menu_text,
            reply_markup=keyboards.get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأزرار التفاعلية"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        session = db.get_user_session(user_id)
        
        try:
            # معالجة الأزرار المختلفة
            if data == "back_to_main":
                await self.show_main_menu(query)
            elif data == "cancel":
                await self.cancel_operation(query)
            elif data == "add_note":
                await self.start_add_note_process(query)
            elif data == "add_note_type":
                await self.start_add_note_process(query)
            elif data == "add_category_type":
                await self.start_add_category_process(query)
            elif data == "view_notes":
                await self.show_all_notes_callback(query)
            elif data == "search_notes":
                await self.start_search_process(query)
            elif data == "edit_menu":
                await self.show_edit_menu(query)
            elif data == "stats":
                await self.show_statistics_callback(query)
            elif data == "backup":
                await self.create_backup_callback(query)
            elif data == "menu":
                await self.show_menu_callback(query)
            elif data.startswith("select_category_"):
                await self.handle_category_selection(query, data)
            elif data.startswith("priority_"):
                await self.handle_priority_selection(query, data)
            elif data.startswith("reminder_"):
                await self.handle_reminder_selection(query, data)
            elif data.startswith("day_"):
                await self.handle_day_selection(query, data)
            elif data.startswith("hour_"):
                await self.handle_hour_selection(query, data)
            elif data.startswith("minute_group_"):
                await self.handle_minute_group_selection(query, data)
            elif data.startswith("minute_"):
                await self.handle_minute_selection(query, data)
            elif data.startswith("view_note_"):
                await self.show_note_details(query, data)
            elif data.startswith("edit_note_"):
                await self.handle_note_edit(query, data)
            elif data.startswith("delete_note_"):
                await self.handle_note_delete(query, data)
            elif data.startswith("confirm_"):
                await self.handle_confirmation(query, data)
            else:
                await query.edit_message_text("❌ خيار غير معروف")
                
        except Exception as e:
            logger.error(f"خطأ في معالجة الزر {data}: {e}")
            await query.edit_message_text("❌ حدث خطأ، يرجى المحاولة مرة أخرى")
    
    async def text_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الرسائل النصية"""
        user_id = update.effective_user.id
        session = db.get_user_session(user_id)
        text = update.message.text.strip()
        
        if not session.current_action:
            # إذا لم تكن هناك عملية جارية، عرض المساعدة
            await update.message.reply_text(
                "💡 لا توجد عملية جارية. استخدم /start لعرض القائمة الرئيسية أو /menu لعرض جميع الأوامر.",
                reply_markup=keyboards.get_main_menu_keyboard()
            )
            return
        
        # معالجة النص حسب العملية الجارية
        if session.current_action == 'add_note':
            await self.handle_add_note_text(update, context, text)
        elif session.current_action == 'add_category':
            await self.handle_add_category_text(update, context, text)
        elif session.current_action == 'search':
            await self.handle_search_text(update, context, text)
        elif session.current_action.startswith('edit_'):
            await self.handle_edit_text(update, context, text)
        else:
            await update.message.reply_text("❌ عملية غير معروفة")
    
    # معالجات العمليات المختلفة
    async def show_main_menu(self, query):
        """عرض القائمة الرئيسية"""
        await query.edit_message_text(
            "🏠 **القائمة الرئيسية**\n\nاختر العملية التي تريد القيام بها:",
            reply_markup=keyboards.get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cancel_operation(self, query):
        """إلغاء العملية الجارية"""
        user_id = query.from_user.id
        db.clear_user_session(user_id)
        
        await query.edit_message_text(
            "❌ تم إلغاء العملية.\n\nاختر عملية أخرى من القائمة:",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
    
    async def start_add_note_process(self, query):
        """بدء عملية إضافة ملاحظة"""
        user_id = query.from_user.id
        session = db.get_user_session(user_id)
        session.set_action('add_note', step=1)
        
        await query.edit_message_text(
            "📝 **إضافة ملاحظة جديدة**\n\n**الخطوة 1/6:** اختر التصنيف:",
            reply_markup=keyboards.get_categories_keyboard(action="select"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def start_add_category_process(self, query):
        """بدء عملية إضافة تصنيف"""
        user_id = query.from_user.id
        session = db.get_user_session(user_id)
        session.set_action('add_category')
        
        await query.edit_message_text(
            "📁 **إضافة تصنيف جديد**\n\nاكتب اسم التصنيف الجديد:",
            reply_markup=keyboards.get_cancel_keyboard()
        )
    
    async def show_all_notes(self, update, context):
        """عرض جميع الملاحظات"""
        notes = db.get_notes()
        
        if not notes:
            await update.message.reply_text(
                "📝 لا توجد ملاحظات حتى الآن.\n\nاستخدم /add لإضافة ملاحظة جديدة.",
                reply_markup=keyboards.get_main_menu_keyboard()
            )
            return
        
        # تجميع الملاحظات حسب التصنيف
        categories_notes = {}
        for note in notes:
            if note.category not in categories_notes:
                categories_notes[note.category] = []
            categories_notes[note.category].append(note)
        
        message_text = "📚 **جميع الملاحظات:**\n\n"
        
        for category, cat_notes in categories_notes.items():
            message_text += f"📁 **{category}** ({len(cat_notes)} ملاحظات)\n"
            message_text += "─" * 30 + "\n"
            
            # عرض أول 5 ملاحظات من كل تصنيف
            for i, note in enumerate(cat_notes[:5]):
                message_text += f"{note.format_for_display(show_category=False, show_id=False)}\n"
            
            if len(cat_notes) > 5:
                message_text += f"... و {len(cat_notes) - 5} ملاحظات أخرى\n"
            
            message_text += "\n"
        
        await update.message.reply_text(
            message_text,
            reply_markup=keyboards.get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_all_notes_callback(self, query):
        """عرض جميع الملاحظات (من الزر)"""
        notes = db.get_notes()
        
        if not notes:
            await query.edit_message_text(
                "📝 لا توجد ملاحظات حتى الآن.\n\nاستخدم إضافة ملاحظة لإنشاء ملاحظة جديدة.",
                reply_markup=keyboards.get_main_menu_keyboard()
            )
            return
        
        # تجميع الملاحظات حسب التصنيف
        categories_notes = {}
        for note in notes:
            if note.category not in categories_notes:
                categories_notes[note.category] = []
            categories_notes[note.category].append(note)
        
        message_text = "📚 **جميع الملاحظات:**\n\n"
        
        for category, cat_notes in categories_notes.items():
            message_text += f"📁 **{category}** ({len(cat_notes)} ملاحظات)\n"
            message_text += "─" * 30 + "\n"
            
            # عرض أول 5 ملاحظات من كل تصنيف
            for i, note in enumerate(cat_notes[:5]):
                message_text += f"{note.format_for_display(show_category=False, show_id=False)}\n"
            
            if len(cat_notes) > 5:
                message_text += f"... و {len(cat_notes) - 5} ملاحظات أخرى\n"
            
            message_text += "\n"
        
        await query.edit_message_text(
            message_text,
            reply_markup=keyboards.get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # سيتم إضافة باقي المعالجات...
    
    async def send_reminder(self, note: Note):
        """إرسال تذكير للمستخدم"""
        # هذه الدالة ستحتاج لمعرف المستخدم
        # في التطبيق الحقيقي، يجب حفظ معرف المستخدم مع كل ملاحظة
        try:
            reminder_text = f"""
⏰ **تذكير مهم!**

{note.get_priority_emoji()} **{note.title}**

📝 {note.content}

📁 التصنيف: {note.category}
🎯 الأولوية: {note.get_priority_text()}
📅 تم إنشاؤها: {note.created_at.strftime('%Y-%m-%d %H:%M')}
            """
            
            # إرسال التذكير (يحتاج لتطوير إضافي لربطه بمعرف المستخدم)
            logger.info(f"تذكير للملاحظة: {note.title}")
            
        except Exception as e:
            logger.error(f"خطأ في إرسال التذكير: {e}")
    
    def run(self):
        """تشغيل البوت"""
        logger.info("بدء تشغيل البوت...")
        
        # إعداد التطبيق
        self.setup_application()
        
        # بدء نظام التذكيرات
        reminder_system.start()
        
        # تشغيل البوت
        self.app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

# باقي المعالجات ستكون في الجزء التالي...