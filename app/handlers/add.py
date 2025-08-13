from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from telegram import Update
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from app.data_store import DataStore
from app.keyboards import (
    build_category_keyboard,
    build_priority_keyboard,
    build_reminder_quick_keyboard,
)

CHOOSE_TYPE, CHOOSE_CATEGORY, ADD_CATEGORY_NAME, ASK_TITLE, ASK_TEXT, CHOOSE_PRIORITY, CHOOSE_REMINDER, CUSTOM_DAY, CUSTOM_HOUR, CUSTOM_MIN_GROUP, CUSTOM_MINUTE = range(11)


def start_add(update: Update, context: CallbackContext) -> int:
    keyboard = [[
        {"text": "📝 ملاحظة", "cb": "type:note"},
        {"text": "📁 تصنيف", "cb": "type:cat"},
    ]]
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 ملاحظة", callback_data="type:note"), InlineKeyboardButton("📁 تصنيف", callback_data="type:cat")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
    ])
    update.message.reply_text("هل تريد إضافة ملاحظة أم تصنيف؟", reply_markup=kb)
    return CHOOSE_TYPE


def on_choose_type(update: Update, context: CallbackContext, store: DataStore) -> int:
    query = update.callback_query
    query.answer()
    data = query.data
    if data == "cancel":
        query.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "type:cat":
        query.edit_message_text("أدخل اسم التصنيف الجديد:")
        context.user_data["add_type"] = "cat"
        return ADD_CATEGORY_NAME
    context.user_data["add_type"] = "note"
    user_id = str(update.effective_user.id)
    cats = store.list_categories(user_id)
    cat_keyboard = build_category_keyboard([(c["id"], c["name"]) for c in cats], include_add=True)
    query.edit_message_text("اختر التصنيف:", reply_markup=cat_keyboard)
    return CHOOSE_CATEGORY


def on_choose_category(update: Update, context: CallbackContext, store: DataStore) -> int:
    query = update.callback_query
    query.answer()
    data = query.data
    user_id = str(update.effective_user.id)
    if data == "cancel":
        query.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "cat_add:new":
        query.edit_message_text("أدخل اسم التصنيف الجديد:")
        context.user_data["adding_new_category"] = True
        return ADD_CATEGORY_NAME
    if data.startswith("cat:"):
        cat_id = data.split(":", 1)[1]
        context.user_data["note_category_id"] = cat_id
        query.edit_message_text("اكتب عنوان الملاحظة:")
        return ASK_TITLE
    query.edit_message_text("خيار غير معروف.")
    return ConversationHandler.END


def add_category_name(update: Update, context: CallbackContext, store: DataStore) -> int:
    user_id = str(update.effective_user.id)
    name = update.message.text.strip()
    store.add_category(user_id, name)
    if context.user_data.get("add_type") == "cat":
        update.message.reply_text("تم إضافة التصنيف بنجاح ✅")
        return ConversationHandler.END
    cats = store.list_categories(user_id)
    from app.keyboards import build_category_keyboard
    cat_keyboard = build_category_keyboard([(c["id"], c["name"]) for c in cats], include_add=True)
    update.message.reply_text("اختر التصنيف:", reply_markup=cat_keyboard)
    return CHOOSE_CATEGORY


def ask_title(update: Update, context: CallbackContext) -> int:
    context.user_data["note_title"] = update.message.text.strip()
    update.message.reply_text("اكتب نص الملاحظة:")
    return ASK_TEXT


def ask_text(update: Update, context: CallbackContext) -> int:
    context.user_data["note_text"] = update.message.text.strip()
    update.message.reply_text("اختر الأولوية:", reply_markup=build_priority_keyboard())
    return CHOOSE_PRIORITY


def choose_priority(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    data = query.data
    if data == "cancel":
        query.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if not data.startswith("prio:"):
        query.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    prio = data.split(":", 1)[1]
    context.user_data["note_priority"] = prio
    query.edit_message_text("اختر التذكير:", reply_markup=build_reminder_quick_keyboard())
    return CHOOSE_REMINDER


def _tomorrow_at(hour: int) -> datetime:
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)
    return tomorrow


def choose_reminder(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    data = query.data
    if data == "cancel":
        query.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "rem:none":
        context.user_data["reminder"] = {"type": "none", "scheduled": False}
        return _finalize_note(query, context)
    if data == "rem:custom":
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("اليوم", callback_data="day:today"), InlineKeyboardButton("غداً", callback_data="day:tomorrow")],
            [InlineKeyboardButton("بعد غد", callback_data="day:after_tomorrow"), InlineKeyboardButton("الأسبوع القادم", callback_data="day:next_week")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
        ])
        query.edit_message_text("اختر اليوم:", reply_markup=kb)
        return CUSTOM_DAY
    if data.startswith("rem:rel:"):
        rel = data.split(":", 2)[2]
        delta = {
            "30min": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "2h": timedelta(hours=2),
            "6h": timedelta(hours=6),
        }.get(rel, timedelta(hours=1))
        run_at = datetime.now(timezone.utc) + delta
        context.user_data["reminder"] = {"type": "absolute", "at_iso": run_at.isoformat(), "scheduled": True}
        return _finalize_note(query, context)
    if data == "rem:abs:tomorrow_09":
        run_at = _tomorrow_at(9)
        context.user_data["reminder"] = {"type": "absolute", "at_iso": run_at.isoformat(), "scheduled": True}
        return _finalize_note(query, context)
    if data == "rem:abs:tomorrow_18":
        run_at = _tomorrow_at(18)
        context.user_data["reminder"] = {"type": "absolute", "at_iso": run_at.isoformat(), "scheduled": True}
        return _finalize_note(query, context)
    query.edit_message_text("خيار غير معروف.")
    return ConversationHandler.END


def custom_day(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    data = query.data
    now = datetime.now(timezone.utc)
    if data == "cancel":
        query.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "day:today":
        context.user_data["custom_base"] = now
    elif data == "day:tomorrow":
        context.user_data["custom_base"] = now + timedelta(days=1)
    elif data == "day:after_tomorrow":
        context.user_data["custom_base"] = now + timedelta(days=2)
    elif data == "day:next_week":
        context.user_data["custom_base"] = now + timedelta(days=7)
    else:
        query.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    hours_row = [InlineKeyboardButton(f"{h:02d}", callback_data=f"hour:{h}") for h in range(0, 24)]
    rows = [hours_row[i:i+6] for i in range(0, 24, 6)]
    rows.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    kb = InlineKeyboardMarkup(rows)
    query.edit_message_text("اختر الساعة (00-23):", reply_markup=kb)
    return CUSTOM_HOUR


def custom_hour(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    data = query.data
    if data == "cancel":
        query.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if not data.startswith("hour:"):
        query.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    hour = int(data.split(":", 1)[1])
    context.user_data["custom_hour"] = hour
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    groups = [(0, 9), (10, 19), (20, 29), (30, 39), (40, 49), (50, 59)]
    rows = [
        [InlineKeyboardButton(f"{a:02d}-{b:02d}", callback_data=f"mgrp:{a}") for a, b in groups],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
    ]
    kb = InlineKeyboardMarkup(rows)
    query.edit_message_text("اختر مجموعة الدقائق:", reply_markup=kb)
    return CUSTOM_MIN_GROUP


def custom_min_group(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    data = query.data
    if data == "cancel":
        query.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if not data.startswith("mgrp:"):
        query.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    start = int(data.split(":", 1)[1])
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    rows = []
    buttons = [InlineKeyboardButton(f"{m:02d}", callback_data=f"min:{m}") for m in range(start, start + 10)]
    rows.extend([buttons[i:i+5] for i in range(0, len(buttons), 5)])
    rows.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    kb = InlineKeyboardMarkup(rows)
    query.edit_message_text("اختر الدقيقة:", reply_markup=kb)
    return CUSTOM_MINUTE


def custom_minute(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    data = query.data
    if data == "cancel":
        query.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if not data.startswith("min:"):
        query.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    minute = int(data.split(":", 1)[1])
    base = context.user_data.get("custom_base")
    hour = context.user_data.get("custom_hour", 9)
    run_at = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    context.user_data["reminder"] = {"type": "absolute", "at_iso": run_at.isoformat(), "scheduled": True}
    return _finalize_note(query, context)


def _finalize_note(query, context: CallbackContext) -> int:
    from app.data_store import DataStore
    store: DataStore = context.bot_data.get("store")
    scheduler = context.bot_data.get("scheduler")
    user_id = str(query.from_user.id)
    cat_id = context.user_data.get("note_category_id", "general")
    title = context.user_data.get("note_title", "")
    text = context.user_data.get("note_text", "")
    prio = context.user_data.get("note_priority", "green")
    reminder = context.user_data.get("reminder", {"type": "none"})
    note_id = store.add_note(user_id, cat_id, title, text, prio, reminder)
    if reminder.get("type") == "absolute" and reminder.get("at_iso"):
        run_at_iso = reminder["at_iso"]
        job_id = scheduler.schedule(int(user_id), int(note_id), run_at_iso) if scheduler else None
        if job_id:
            note = store.get_note(user_id, note_id)
            if note:
                note["reminder"]["job_id"] = job_id
                note["reminder"]["scheduled"] = True
                store.update_note(user_id, note_id, reminder=note["reminder"])
    query.edit_message_text("تم حفظ الملاحظة بنجاح ✅")
    context.user_data.clear()
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    if update.callback_query:
        update.callback_query.answer()
        update.callback_query.edit_message_text("تم الإلغاء.")
    else:
        update.message.reply_text("تم الإلغاء.")
    context.user_data.clear()
    return ConversationHandler.END


def build_add_handler(store: DataStore) -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("add", start_add)],
        states={
            CHOOSE_TYPE: [CallbackQueryHandler(lambda u, c: on_choose_type(u, c, store))],
            CHOOSE_CATEGORY: [CallbackQueryHandler(lambda u, c: on_choose_category(u, c, store))],
            ADD_CATEGORY_NAME: [MessageHandler(Filters.text & ~Filters.command, lambda u, c: add_category_name(u, c, store))],
            ASK_TITLE: [MessageHandler(Filters.text & ~Filters.command, ask_title)],
            ASK_TEXT: [MessageHandler(Filters.text & ~Filters.command, ask_text)],
            CHOOSE_PRIORITY: [CallbackQueryHandler(choose_priority)],
            CHOOSE_REMINDER: [CallbackQueryHandler(choose_reminder)],
            CUSTOM_DAY: [CallbackQueryHandler(custom_day)],
            CUSTOM_HOUR: [CallbackQueryHandler(custom_hour)],
            CUSTOM_MIN_GROUP: [CallbackQueryHandler(custom_min_group)],
            CUSTOM_MINUTE: [CallbackQueryHandler(custom_minute)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(cancel, pattern="^cancel$")],
        name="add_conversation",
        persistent=False,
    )