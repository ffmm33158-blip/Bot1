from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from app.data_store import DataStore
from app.keyboards import build_reminder_quick_keyboard
from datetime import datetime, timedelta, timezone

CHOOSE_EDIT, EDIT_CAT_LIST, EDIT_CAT_ACTION, EDIT_CAT_RENAME, EDIT_NOTE_CAT, EDIT_NOTE_LIST, EDIT_NOTE_ACTION, EDIT_NOTE_TITLE, EDIT_NOTE_TEXT, EDIT_NOTE_PRIO, EDIT_NOTE_REM, EDIT_REM_DAY, EDIT_REM_HOUR, EDIT_REM_MGRP, EDIT_REM_MIN = range(15)


def start_edit(update: Update, context: CallbackContext) -> int:
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 تعديل تصنيف", callback_data="edit:cat"), InlineKeyboardButton("📝 تعديل ملاحظة", callback_data="edit:note")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
    ])
    update.message.reply_text("ماذا تريد تعديل؟", reply_markup=kb)
    return CHOOSE_EDIT


def choose_edit(update: Update, context: CallbackContext, store: DataStore) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    user_id = str(q.from_user.id)
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "edit:cat":
        cats = store.list_categories(user_id)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(c["name"], callback_data=f"cat:{c['id']}")] for c in cats] + [[InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]])
        q.edit_message_text("اختر التصنيف:", reply_markup=kb)
        return EDIT_CAT_LIST
    if data == "edit:note":
        cats = store.list_categories(user_id)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(c["name"], callback_data=f"ncat:{c['id']}")] for c in cats] + [[InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]])
        q.edit_message_text("اختر التصنيف لاختيار ملاحظة:", reply_markup=kb)
        return EDIT_NOTE_CAT
    q.edit_message_text("خيار غير معروف.")
    return ConversationHandler.END


def edit_category_list(update: Update, context: CallbackContext, store: DataStore) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    user_id = str(q.from_user.id)
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data.startswith("cat:"):
        cid = data.split(":", 1)[1]
        context.user_data["edit_cat_id"] = cid
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ إعادة تسمية", callback_data="cact:rename"), InlineKeyboardButton("🗑️ حذف", callback_data="cact:delete")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data="cact:back"), InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
        ])
        q.edit_message_text("اختر الإجراء:", reply_markup=kb)
        return EDIT_CAT_ACTION
    q.edit_message_text("خيار غير معروف.")
    return ConversationHandler.END


def edit_category_action(update: Update, context: CallbackContext, store: DataStore) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    user_id = str(q.from_user.id)
    cid = context.user_data.get("edit_cat_id", "")
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "cact:back":
        cats = store.list_categories(user_id)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(c["name"], callback_data=f"cat:{c['id']}")] for c in cats] + [[InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]])
        q.edit_message_text("اختر التصنيف:", reply_markup=kb)
        return EDIT_CAT_LIST
    if data == "cact:rename":
        q.edit_message_text("أرسل الاسم الجديد:")
        return EDIT_CAT_RENAME
    if data == "cact:delete":
        if cid == "general":
            q.edit_message_text("لا يمكن حذف 'عام'.")
            return ConversationHandler.END
        ok = store.delete_category(user_id, cid)
        q.edit_message_text("تم حذف التصنيف ونقل ملاحظاته إلى 'عام'." if ok else "تعذر الحذف.")
        return ConversationHandler.END
    q.edit_message_text("خيار غير معروف.")
    return ConversationHandler.END


def edit_category_rename(update: Update, context: CallbackContext, store: DataStore) -> int:
    user_id = str(update.effective_user.id)
    cid = context.user_data.get("edit_cat_id", "")
    new_name = update.message.text.strip()
    ok = store.rename_category(user_id, cid, new_name)
    update.message.reply_text("تم التحديث ✅" if ok else "تعذر التحديث")
    return ConversationHandler.END


def edit_note_choose_cat(update: Update, context: CallbackContext, store: DataStore) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    user_id = str(q.from_user.id)
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if not data.startswith("ncat:"):
        q.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    cid = data.split(":", 1)[1]
    context.user_data["note_edit_cat"] = cid
    user = store.get_user_data(user_id)
    notes = [n for n in user.get("notes", []) if n["category_id"] == cid]
    if not notes:
        q.edit_message_text("لا توجد ملاحظات في هذا التصنيف.")
        return ConversationHandler.END
    buttons = [[InlineKeyboardButton(f"#{n['id']} | {n['title'][:20]}", callback_data=f"note:{n['id']}")] for n in notes[:50]]
    buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    q.edit_message_text("اختر الملاحظة:", reply_markup=InlineKeyboardMarkup(buttons))
    return EDIT_NOTE_LIST


def edit_note_list(update: Update, context: CallbackContext, store: DataStore) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    user_id = str(q.from_user.id)
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if not data.startswith("note:"):
        q.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    nid = int(data.split(":", 1)[1])
    context.user_data["edit_note_id"] = nid
    note = store.get_note(user_id, nid)
    if not note:
        q.edit_message_text("لم يتم العثور على الملاحظة.")
        return ConversationHandler.END
    rem = note.get("reminder", {}) or {}
    at = rem.get("at_iso")
    rem_text = "بدون" if rem.get("type") in (None, "none") else (at or "(غير محدد)")
    preview = f"العنوان: {note.get('title','')}\nالنص: {note.get('text','')[:50]}...\nالأولوية: {note.get('priority','green')}\nالتذكير: {rem_text}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ عنوان", callback_data="nact:title"), InlineKeyboardButton("📄 نص", callback_data="nact:text")],
        [InlineKeyboardButton("⭐ أولوية", callback_data="nact:prio"), InlineKeyboardButton("⏰ تذكير", callback_data="nact:rem"), InlineKeyboardButton("🗑️ حذف", callback_data="nact:delete")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
    ])
    q.edit_message_text(f"الملاحظة:\n{preview}\n\nاختر ما تريد تعديله:", reply_markup=kb)
    return EDIT_NOTE_ACTION


def edit_note_action(update: Update, context: CallbackContext, store: DataStore) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    user_id = str(q.from_user.id)
    nid = int(context.user_data.get("edit_note_id", 0))
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "nact:delete":
        ok = store.delete_note(user_id, nid)
        q.edit_message_text("تم حذف الملاحظة." if ok else "تعذر الحذف.")
        return ConversationHandler.END
    if data == "nact:title":
        q.edit_message_text("أرسل العنوان الجديد:")
        return EDIT_NOTE_TITLE
    if data == "nact:text":
        q.edit_message_text("أرسل النص الجديد:")
        return EDIT_NOTE_TEXT
    if data == "nact:prio":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔴", callback_data="prio:red"), InlineKeyboardButton("🟡", callback_data="prio:yellow"), InlineKeyboardButton("🟢", callback_data="prio:green")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
        ])
        q.edit_message_text("اختر أولوية:", reply_markup=kb)
        return EDIT_NOTE_PRIO
    if data == "nact:rem":
        q.edit_message_text("اختر التذكير:", reply_markup=build_reminder_quick_keyboard())
        return EDIT_NOTE_REM
    q.edit_message_text("خيار غير معروف.")
    return ConversationHandler.END


def edit_note_title(update: Update, context: CallbackContext, store: DataStore) -> int:
    user_id = str(update.effective_user.id)
    nid = int(context.user_data.get("edit_note_id", 0))
    title = update.message.text.strip()
    ok = store.update_note(user_id, nid, title=title)
    update.message.reply_text("تم التحديث ✅" if ok else "تعذر التحديث")
    return ConversationHandler.END


def edit_note_text(update: Update, context: CallbackContext, store: DataStore) -> int:
    user_id = str(update.effective_user.id)
    nid = int(context.user_data.get("edit_note_id", 0))
    text = update.message.text.strip()
    ok = store.update_note(user_id, nid, text=text)
    update.message.reply_text("تم التحديث ✅" if ok else "تعذر التحديث")
    return ConversationHandler.END


def edit_note_prio(update: Update, context: CallbackContext, store: DataStore) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    user_id = str(q.from_user.id)
    nid = int(context.user_data.get("edit_note_id", 0))
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if not data.startswith("prio:"):
        q.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    pr = data.split(":", 1)[1]
    ok = store.update_note(user_id, nid, priority=pr)
    q.edit_message_text("تم التحديث ✅" if ok else "تعذر التحديث")
    return ConversationHandler.END


# Reminder editing flow

def _tomorrow_at(hour: int) -> datetime:
    now = datetime.now(timezone.utc)
    return (now + timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)


def edit_note_reminder(update: Update, context: CallbackContext, store: DataStore) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    user_id = str(q.from_user.id)
    nid = int(context.user_data.get("edit_note_id", 0))
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "rem:none":
        # Cancel existing job if any
        scheduler = context.bot_data.get("scheduler")
        note = store.get_note(user_id, nid)
        if note and note.get("reminder", {}).get("job_id"):
            try:
                scheduler.cancel(note["reminder"]["job_id"])  # type: ignore[attr-defined]
            except Exception:
                pass
        new_rem = {"type": "none", "scheduled": False, "job_id": None, "at_iso": None}
        ok = store.update_note(user_id, nid, reminder=new_rem)
        q.edit_message_text("تم إزالة التذكير" if ok else "تعذر التحديث")
        return ConversationHandler.END
    if data == "rem:custom":
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("اليوم", callback_data="eday:today"), InlineKeyboardButton("غداً", callback_data="eday:tomorrow")],
            [InlineKeyboardButton("بعد غد", callback_data="eday:after_tomorrow"), InlineKeyboardButton("الأسبوع القادم", callback_data="eday:next_week")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
        ])
        q.edit_message_text("اختر اليوم:", reply_markup=kb)
        return EDIT_REM_DAY
    if data.startswith("rem:rel:"):
        rel = data.split(":", 2)[2]
        delta = {
            "30min": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "2h": timedelta(hours=2),
            "6h": timedelta(hours=6),
        }.get(rel, timedelta(hours=1))
        run_at = datetime.now(timezone.utc) + delta
        return _finalize_reminder(q, context, store, run_at)
    if data == "rem:abs:tomorrow_09":
        return _finalize_reminder(q, context, store, _tomorrow_at(9))
    if data == "rem:abs:tomorrow_18":
        return _finalize_reminder(q, context, store, _tomorrow_at(18))
    q.edit_message_text("خيار غير معروف.")
    return ConversationHandler.END


def edit_rem_day(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    now = datetime.now(timezone.utc)
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "eday:today":
        context.user_data["custom_base"] = now
    elif data == "eday:tomorrow":
        context.user_data["custom_base"] = now + timedelta(days=1)
    elif data == "eday:after_tomorrow":
        context.user_data["custom_base"] = now + timedelta(days=2)
    elif data == "eday:next_week":
        context.user_data["custom_base"] = now + timedelta(days=7)
    else:
        q.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    hours_row = [InlineKeyboardButton(f"{h:02d}", callback_data=f"ehour:{h}") for h in range(0, 24)]
    rows = [hours_row[i:i+6] for i in range(0, 24, 6)]
    rows.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    kb = InlineKeyboardMarkup(rows)
    q.edit_message_text("اختر الساعة (00-23):", reply_markup=kb)
    return EDIT_REM_HOUR


def edit_rem_hour(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if not data.startswith("ehour:"):
        q.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    hour = int(data.split(":", 1)[1])
    context.user_data["custom_hour"] = hour
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    groups = [(0, 9), (10, 19), (20, 29), (30, 39), (40, 49), (50, 59)]
    rows = [
        [InlineKeyboardButton(f"{a:02d}-{b:02d}", callback_data=f"emgrp:{a}") for a, b in groups],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
    ]
    kb = InlineKeyboardMarkup(rows)
    q.edit_message_text("اختر مجموعة الدقائق:", reply_markup=kb)
    return EDIT_REM_MGRP


def edit_rem_mgrp(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if not data.startswith("emgrp:"):
        q.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    start = int(data.split(":", 1)[1])
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    rows = []
    buttons = [InlineKeyboardButton(f"{m:02d}", callback_data=f"emin:{m}") for m in range(start, start + 10)]
    rows.extend([buttons[i:i+5] for i in range(0, len(buttons), 5)])
    rows.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    kb = InlineKeyboardMarkup(rows)
    q.edit_message_text("اختر الدقيقة:", reply_markup=kb)
    return EDIT_REM_MIN


def edit_rem_min(update: Update, context: CallbackContext, store: DataStore) -> int:
    q = update.callback_query
    q.answer()
    data = q.data
    if data == "cancel":
        q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if not data.startswith("emin:"):
        q.edit_message_text("خيار غير معروف.")
        return ConversationHandler.END
    minute = int(data.split(":", 1)[1])
    base = context.user_data.get("custom_base")
    hour = context.user_data.get("custom_hour", 9)
    run_at = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return _finalize_reminder(q, context, store, run_at)


def _finalize_reminder(q, context: CallbackContext, store: DataStore, run_at: datetime) -> int:
    user_id = str(q.from_user.id)
    nid = int(context.user_data.get("edit_note_id", 0))
    scheduler = context.bot_data.get("scheduler")
    note = store.get_note(user_id, nid)
    # Cancel old
    if note and note.get("reminder", {}).get("job_id"):
        try:
            scheduler.cancel(note["reminder"]["job_id"])  # type: ignore[attr-defined]
        except Exception:
            pass
    at_iso = run_at.isoformat()
    job_id = scheduler.schedule(int(user_id), int(nid), at_iso) if scheduler else None  # type: ignore[attr-defined]
    new_rem = {"type": "absolute", "at_iso": at_iso, "scheduled": bool(job_id), "job_id": job_id}
    ok = store.update_note(user_id, nid, reminder=new_rem)
    q.edit_message_text("تم تحديث التذكير ✅" if ok else "تعذر التحديث")
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    if update.callback_query:
        update.callback_query.answer()
        update.callback_query.edit_message_text("تم الإلغاء.")
    else:
        update.message.reply_text("تم الإلغاء.")
    context.user_data.clear()
    return ConversationHandler.END


def build_edit_handler(store: DataStore) -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("edit", start_edit)],
        states={
            CHOOSE_EDIT: [CallbackQueryHandler(lambda u, c: choose_edit(u, c, store))],
            EDIT_CAT_LIST: [CallbackQueryHandler(lambda u, c: edit_category_list(u, c, store))],
            EDIT_CAT_ACTION: [CallbackQueryHandler(lambda u, c: edit_category_action(u, c, store))],
            EDIT_CAT_RENAME: [MessageHandler(Filters.text & ~Filters.command, lambda u, c: edit_category_rename(u, c, store))],
            EDIT_NOTE_CAT: [CallbackQueryHandler(lambda u, c: edit_note_choose_cat(u, c, store))],
            EDIT_NOTE_LIST: [CallbackQueryHandler(lambda u, c: edit_note_list(u, c, store))],
            EDIT_NOTE_ACTION: [CallbackQueryHandler(lambda u, c: edit_note_action(u, c, store))],
            EDIT_NOTE_TITLE: [MessageHandler(Filters.text & ~Filters.command, lambda u, c: edit_note_title(u, c, store))],
            EDIT_NOTE_TEXT: [MessageHandler(Filters.text & ~Filters.command, lambda u, c: edit_note_text(u, c, store))],
            EDIT_NOTE_PRIO: [CallbackQueryHandler(lambda u, c: edit_note_prio(u, c, store))],
            EDIT_NOTE_REM: [CallbackQueryHandler(lambda u, c: edit_note_reminder(u, c, store))],
            EDIT_REM_DAY: [CallbackQueryHandler(edit_rem_day)],
            EDIT_REM_HOUR: [CallbackQueryHandler(edit_rem_hour)],
            EDIT_REM_MGRP: [CallbackQueryHandler(edit_rem_mgrp)],
            EDIT_REM_MIN: [CallbackQueryHandler(lambda u, c: edit_rem_min(u, c, store))],
        },
        fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(cancel, pattern="^cancel$")],
        name="edit_conversation",
        persistent=False,
    )