#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import PRIORITY_COLORS, MAX_SEARCH_RESULTS
from database import db
from keyboards import keyboards
from reminder_system import reminder_helper, ReminderSystem

logger = logging.getLogger(__name__)

class BotHandlers:
    """معالجات إضافية للبوت"""
    
    @staticmethod
    async def handle_category_selection(bot_instance, query, data):
        """معالج اختيار التصنيف"""
        user_id = query.from_user.id
        session = db.get_user_session(user_id)
        
        category_name = data.replace("select_category_", "")
        session.update_temp_data(category=category_name)
        session.next_step()  # الخطوة 2
        
        await query.edit_message_text(
            f"📝 **إضافة ملاحظة جديدة**\n\n**الخطوة 2/6:** اكتب عنوان الملاحظة:\n\n📁 التصنيف المختار: **{category_name}**",
            reply_markup=keyboards.get_cancel_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    @staticmethod
    async def handle_priority_selection(bot_instance, query, data):
        """معالج اختيار الأولوية"""
        user_id = query.from_user.id
        session = db.get_user_session(user_id)
        
        priority = data.replace("priority_", "")
        session.update_temp_data(priority=priority)
        session.next_step()  # الخطوة 5
        
        priority_info = PRIORITY_COLORS[priority]
        
        await query.edit_message_text(
            f"📝 **إضافة ملاحظة جديدة**\n\n**الخطوة 5/6:** اختر نوع التذكير:\n\n"
            f"📁 التصنيف: **{session.temp_data.get('category')}**\n"
            f"🎯 العنوان: **{session.temp_data.get('title')}**\n"
            f"📝 النص: **{session.temp_data.get('content')[:30]}...**\n"
            f"🎯 الأولوية: **{priority_info['emoji']} {priority_info['text']}**",
            reply_markup=keyboards.get_reminder_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    @staticmethod
    async def handle_reminder_selection(bot_instance, query, data):
        """معالج اختيار التذكير"""
        user_id = query.from_user.id
        session = db.get_user_session(user_id)
        
        reminder_type = data.replace("reminder_", "")
        
        if reminder_type == "custom":
            # بدء عملية الوقت المخصص
            session.update_temp_data(reminder_type="custom")
            
            await query.edit_message_text(
                "📝 **إضافة ملاحظة جديدة**\n\n**الخطوة 6/6:** اختيار الوقت المخصص\n\n**اختر اليوم:**",
                reply_markup=keyboards.get_custom_time_day_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # حساب وقت التذكير وإنشاء الملاحظة
            reminder_time = ReminderSystem.calculate_reminder_time(reminder_type)
            await BotHandlers._create_note_final(query, session, reminder_time)
    
    @staticmethod
    async def handle_day_selection(bot_instance, query, data):
        """معالج اختيار اليوم للوقت المخصص"""
        user_id = query.from_user.id
        session = db.get_user_session(user_id)
        
        day = reminder_helper.parse_day_selection(data)
        session.update_temp_data(custom_day=day)
        
        day_name = reminder_helper.get_day_display_name(day)
        
        await query.edit_message_text(
            f"📝 **إضافة ملاحظة جديدة**\n\n**الخطوة 6/6:** اختيار الوقت المخصص\n\n"
            f"📅 اليوم المختار: **{day_name}**\n\n**اختر الساعة:**",
            reply_markup=keyboards.get_custom_time_hour_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    @staticmethod
    async def handle_hour_selection(bot_instance, query, data):
        """معالج اختيار الساعة"""
        user_id = query.from_user.id
        session = db.get_user_session(user_id)
        
        hour = reminder_helper.parse_hour_selection(data)
        session.update_temp_data(custom_hour=hour)
        
        day_name = reminder_helper.get_day_display_name(session.temp_data.get('custom_day'))
        
        await query.edit_message_text(
            f"📝 **إضافة ملاحظة جديدة**\n\n**الخطوة 6/6:** اختيار الوقت المخصص\n\n"
            f"📅 اليوم: **{day_name}**\n"
            f"🕐 الساعة: **{hour:02d}:xx**\n\n**اختر مجموعة الدقائق:**",
            reply_markup=keyboards.get_custom_time_minute_group_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    @staticmethod
    async def handle_minute_group_selection(bot_instance, query, data):
        """معالج اختيار مجموعة الدقائق"""
        user_id = query.from_user.id
        session = db.get_user_session(user_id)
        
        minute_group = reminder_helper.parse_minute_group_selection(data)
        session.update_temp_data(custom_minute_group=minute_group)
        
        day_name = reminder_helper.get_day_display_name(session.temp_data.get('custom_day'))
        hour = session.temp_data.get('custom_hour')
        
        await query.edit_message_text(
            f"📝 **إضافة ملاحظة جديدة**\n\n**الخطوة 6/6:** اختيار الوقت المخصص\n\n"
            f"📅 اليوم: **{day_name}**\n"
            f"🕐 الساعة: **{hour:02d}:{minute_group:02d}-{minute_group+9:02d}**\n\n**اختر الدقيقة الدقيقة:**",
            reply_markup=keyboards.get_custom_time_minute_keyboard(minute_group),
            parse_mode=ParseMode.MARKDOWN
        )
    
    @staticmethod
    async def handle_minute_selection(bot_instance, query, data):
        """معالج اختيار الدقيقة النهائية"""
        user_id = query.from_user.id
        session = db.get_user_session(user_id)
        
        minute = reminder_helper.parse_minute_selection(data)
        
        # حساب الوقت المخصص
        day = session.temp_data.get('custom_day')
        hour = session.temp_data.get('custom_hour')
        
        reminder_time = ReminderSystem.calculate_reminder_time(
            'custom',
            day=day,
            hour=hour,
            minute=minute
        )
        
        await BotHandlers._create_note_final(query, session, reminder_time)
    
    @staticmethod
    async def _create_note_final(query, session, reminder_time):
        """إنشاء الملاحظة النهائية"""
        try:
            # إنشاء الملاحظة
            note = db.add_note(
                title=session.temp_data['title'],
                content=session.temp_data['content'],
                category=session.temp_data['category'],
                priority=session.temp_data['priority'],
                reminder_time=reminder_time
            )
            
            # تنسيق رسالة النجاح
            reminder_text = "🚫 بدون تذكير"
            if reminder_time:
                reminder_text = ReminderSystem.format_reminder_time(reminder_time)
            
            success_message = f"""
✅ **تم إنشاء الملاحظة بنجاح!**

{note.format_for_display()}

⏰ التذكير: {reminder_text}
📅 تاريخ الإنشاء: {note.created_at.strftime('%Y-%m-%d %H:%M')}
            """
            
            # مسح الجلسة
            db.clear_user_session(query.from_user.id)
            
            await query.edit_message_text(
                success_message,
                reply_markup=keyboards.get_main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء الملاحظة: {e}")
            await query.edit_message_text(
                "❌ حدث خطأ أثناء إنشاء الملاحظة. يرجى المحاولة مرة أخرى.",
                reply_markup=keyboards.get_main_menu_keyboard()
            )
    
    @staticmethod
    async def handle_add_note_text(bot_instance, update, context, text):
        """معالج النص لإضافة الملاحظة"""
        user_id = update.effective_user.id
        session = db.get_user_session(user_id)
        
        if session.step == 2:  # عنوان الملاحظة
            session.update_temp_data(title=text)
            session.next_step()
            
            await update.message.reply_text(
                f"📝 **إضافة ملاحظة جديدة**\n\n**الخطوة 3/6:** اكتب نص الملاحظة:\n\n"
                f"📁 التصنيف: **{session.temp_data.get('category')}**\n"
                f"🎯 العنوان: **{text}**",
                reply_markup=keyboards.get_cancel_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif session.step == 3:  # نص الملاحظة
            session.update_temp_data(content=text)
            session.next_step()
            
            await update.message.reply_text(
                f"📝 **إضافة ملاحظة جديدة**\n\n**الخطوة 4/6:** اختر الأولوية:\n\n"
                f"📁 التصنيف: **{session.temp_data.get('category')}**\n"
                f"🎯 العنوان: **{session.temp_data.get('title')}**\n"
                f"📝 النص: **{text[:50]}...**",
                reply_markup=keyboards.get_priority_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    @staticmethod
    async def handle_add_category_text(bot_instance, update, context, text):
        """معالج النص لإضافة التصنيف"""
        user_id = update.effective_user.id
        
        if db.add_category(text):
            db.clear_user_session(user_id)
            
            await update.message.reply_text(
                f"✅ **تم إضافة التصنيف بنجاح!**\n\n📁 **{text}**\n\nيمكنك الآن استخدام هذا التصنيف عند إضافة ملاحظات جديدة.",
                reply_markup=keyboards.get_main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"❌ **التصنيف موجود بالفعل!**\n\nالتصنيف **{text}** موجود مسبقاً. اكتب اسم تصنيف آخر:",
                reply_markup=keyboards.get_cancel_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    @staticmethod
    async def handle_search_text(bot_instance, update, context, text):
        """معالج النص للبحث"""
        user_id = update.effective_user.id
        
        # البحث في الملاحظات
        results = db.search_notes(text)
        
        if not results:
            await update.message.reply_text(
                f"🔍 **نتائج البحث عن: \"{text}\"**\n\n❌ لا توجد نتائج مطابقة.\n\nجرب كلمات أخرى أو تأكد من الإملاء.",
                reply_markup=keyboards.get_main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            message_text = f"🔍 **نتائج البحث عن: \"{text}\"**\n\n📊 تم العثور على **{len(results)}** نتيجة:\n\n"
            
            for i, note in enumerate(results, 1):
                message_text += f"**{i}.** {note.format_for_display()}\n\n"
            
            if len(results) == MAX_SEARCH_RESULTS:
                message_text += "💡 *عرض أول 10 نتائج فقط. جرب بحث أكثر تحديداً للحصول على نتائج أفضل.*"
            
            await update.message.reply_text(
                message_text,
                reply_markup=keyboards.get_main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # مسح الجلسة
        db.clear_user_session(user_id)
    
    @staticmethod
    async def show_statistics(bot_instance, update, context):
        """عرض الإحصائيات"""
        stats = db.get_stats()
        
        message_text = "📊 **إحصائيات مفصلة**\n\n"
        
        # الإحصائيات العامة
        message_text += f"📝 إجمالي الملاحظات: **{stats['total_notes']}**\n"
        message_text += f"📁 إجمالي التصنيفات: **{stats['total_categories']}**\n"
        message_text += f"🆕 الملاحظات الحديثة (آخر 7 أيام): **{stats['recent_notes']}**\n\n"
        
        # إحصائيات التصنيفات
        if stats['category_stats']:
            message_text += "📁 **تفصيل التصنيفات:**\n"
            for category, count in stats['category_stats'].items():
                message_text += f"   • {category}: **{count}** ملاحظات\n"
            message_text += "\n"
        
        # إحصائيات الأولويات
        priority_emojis = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        priority_names = {'high': 'مهم جداً', 'medium': 'مهم', 'low': 'عادي'}
        
        message_text += "🎯 **توزيع الأولويات:**\n"
        for priority, count in stats['priority_stats'].items():
            emoji = priority_emojis.get(priority, '⚪')
            name = priority_names.get(priority, priority)
            message_text += f"   • {emoji} {name}: **{count}** ملاحظات\n"
        
        await update.message.reply_text(
            message_text,
            reply_markup=keyboards.get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    @staticmethod
    async def show_statistics_callback(bot_instance, query):
        """عرض الإحصائيات (من الزر)"""
        stats = db.get_stats()
        
        message_text = "📊 **إحصائيات مفصلة**\n\n"
        
        # الإحصائيات العامة
        message_text += f"📝 إجمالي الملاحظات: **{stats['total_notes']}**\n"
        message_text += f"📁 إجمالي التصنيفات: **{stats['total_categories']}**\n"
        message_text += f"🆕 الملاحظات الحديثة (آخر 7 أيام): **{stats['recent_notes']}**\n\n"
        
        # إحصائيات التصنيفات
        if stats['category_stats']:
            message_text += "📁 **تفصيل التصنيفات:**\n"
            for category, count in stats['category_stats'].items():
                message_text += f"   • {category}: **{count}** ملاحظات\n"
            message_text += "\n"
        
        # إحصائيات الأولويات
        priority_emojis = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        priority_names = {'high': 'مهم جداً', 'medium': 'مهم', 'low': 'عادي'}
        
        message_text += "🎯 **توزيع الأولويات:**\n"
        for priority, count in stats['priority_stats'].items():
            emoji = priority_emojis.get(priority, '⚪')
            name = priority_names.get(priority, priority)
            message_text += f"   • {emoji} {name}: **{count}** ملاحظات\n"
        
        await query.edit_message_text(
            message_text,
            reply_markup=keyboards.get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    @staticmethod
    async def create_backup(bot_instance, update, context):
        """إنشاء نسخة احتياطية"""
        try:
            backup_path = db.create_backup_file()
            
            with open(backup_path, 'rb') as backup_file:
                await update.message.reply_document(
                    document=backup_file,
                    caption="💾 **نسخة احتياطية من ملاحظاتك**\n\nتم إنشاء النسخة الاحتياطية بنجاح! يمكنك حفظ هذا الملف كنسخة احتياطية آمنة.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboards.get_main_menu_keyboard()
                )
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            await update.message.reply_text(
                "❌ حدث خطأ أثناء إنشاء النسخة الاحتياطية. يرجى المحاولة مرة أخرى.",
                reply_markup=keyboards.get_main_menu_keyboard()
            )
    
    @staticmethod
    async def create_backup_callback(bot_instance, query):
        """إنشاء نسخة احتياطية (من الزر)"""
        try:
            backup_path = db.create_backup_file()
            
            await query.answer("جاري إنشاء النسخة الاحتياطية...")
            
            with open(backup_path, 'rb') as backup_file:
                await query.message.reply_document(
                    document=backup_file,
                    caption="💾 **نسخة احتياطية من ملاحظاتك**\n\nتم إنشاء النسخة الاحتياطية بنجاح! يمكنك حفظ هذا الملف كنسخة احتياطية آمنة.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboards.get_main_menu_keyboard()
                )
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            await query.edit_message_text(
                "❌ حدث خطأ أثناء إنشاء النسخة الاحتياطية. يرجى المحاولة مرة أخرى.",
                reply_markup=keyboards.get_main_menu_keyboard()
            )

# إنشاء مثيل واحد من المعالجات
bot_handlers = BotHandlers()