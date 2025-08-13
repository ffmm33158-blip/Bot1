import os
import json
import logging
import http.server
import socketserver
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

############################################################
# إعداد التسجيل
############################################################
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

############################################################
# تكوين عام
############################################################
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATA_FILE = os.getenv("DATA_FILE", "notes_data.json")
BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
AUTO_BACKUP_DIR = os.getenv("AUTO_BACKUP_DIR", os.path.join(BACKUP_DIR, "auto"))
WEB_PORT = int(os.getenv("PORT", "8000"))

DEFAULT_CATEGORIES = ["عام", "مهام", "أفكار"]

PRIORITY_LABELS = {
    "high": "🔴 مهم جداً",
    "medium": "🟡 مهم",
    "low": "🟢 عادي",
}

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

############################################################
# نماذج البيانات
############################################################
@dataclass
class Note:
    note_id: int
    category: str
    title: str
    body: str
    priority: str  # high | medium | low
    created_at: str  # ISO
    reminder_at: Optional[str] = None  # ISO

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "Note":
        return Note(**data)


############################################################
# إدارة البيانات
############################################################
class NotesStore:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.data = self._load()
        os.makedirs(BACKUP_DIR, exist_ok=True)
        os.makedirs(AUTO_BACKUP_DIR, exist_ok=True)

        # تهيئة الحقول الأساسية
        self.data.setdefault("notes", [])
        self.data.setdefault("categories", list(DEFAULT_CATEGORIES))
        self.data.setdefault("last_note_id", 0)
        self.data.setdefault("test_count", 0)
        self.data.setdefault("last_test", None)
        self._save(auto_backup=False)  # ضمان وجود الملف

    def _load(self) -> Dict:
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"خطأ في تحميل البيانات: {e}")
        return {}

    def _save(self, auto_backup: bool = True) -> None:
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            if auto_backup:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                auto_backup_path = os.path.join(
                    AUTO_BACKUP_DIR, f"notes_auto_{ts}.json"
                )
                with open(auto_backup_path, "w", encoding="utf-8") as bf:
                    json.dump(self.data, bf, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"خطأ في حفظ البيانات: {e}")

    # أدوات مساعدة
    def _next_id(self) -> int:
        self.data["last_note_id"] += 1
        return self.data["last_note_id"]

    def ensure_category(self, category: str) -> None:
        if category not in self.data["categories"]:
            self.data["categories"].append(category)
            self._save()

    # عمليات على الملاحظات
    def add_note(
        self,
        category: str,
        title: str,
        body: str,
        priority: str,
        reminder_at: Optional[datetime] = None,
    ) -> Note:
        self.ensure_category(category)
        note = Note(
            note_id=self._next_id(),
            category=category,
            title=title.strip(),
            body=body.strip(),
            priority=priority,
            created_at=datetime.now().isoformat(),
            reminder_at=reminder_at.isoformat() if reminder_at else None,
        )
        self.data["notes"].append(note.to_dict())
        self._save()
        return note

    def get_notes(self) -> List[Note]:
        return [Note.from_dict(n) for n in self.data.get("notes", [])]

    def get_note(self, note_id: int) -> Optional[Note]:
        for n in self.data.get("notes", []):
            if n.get("note_id") == note_id:
                return Note.from_dict(n)
        return None

    def update_note(self, updated_note: Note) -> bool:
        for idx, n in enumerate(self.data.get("notes", [])):
            if n.get("note_id") == updated_note.note_id:
                self.data["notes"][idx] = updated_note.to_dict()
                self._save()
                return True
        return False

    def delete_note(self, note_id: int) -> bool:
        notes = self.data.get("notes", [])
        for idx, n in enumerate(notes):
            if n.get("note_id") == note_id:
                del notes[idx]
                self._save()
                return True
        return False

    # عمليات على التصنيفات
    def list_categories(self) -> List[str]:
        return list(self.data.get("categories", []))

    def add_category(self, name: str) -> None:
        if name not in self.data["categories"]:
            self.data["categories"].append(name)
            self._save()

    def rename_category(self, old: str, new: str) -> bool:
        cats = self.data.get("categories", [])
        if old in cats and new not in cats:
            for i, c in enumerate(cats):
                if c == old:
                    cats[i] = new
                    break
            # تحديث الملاحظات التابعة
            for n in self.data.get("notes", []):
                if n.get("category") == old:
                    n["category"] = new
            self._save()
            return True
        return False

    def delete_category(self, name: str) -> bool:
        cats = self.data.get("categories", [])
        if name in cats and name != "عام":
            # نقل الملاحظات إلى "عام"
            for n in self.data.get("notes", []):
                if n.get("category") == name:
                    n["category"] = "عام"
            cats.remove(name)
            if "عام" not in cats:
                cats.append("عام")
            self._save()
            return True
        return False

    # مساعدات أخرى
    def increment_test(self) -> int:
        self.data["test_count"] = int(self.data.get("test_count", 0)) + 1
        self.data["last_test"] = datetime.now().isoformat()
        self._save()
        return self.data["test_count"]

    def stats(self) -> Dict:
        notes = self.get_notes()
        total = len(notes)
        cats = self.list_categories()
        recent_cut = datetime.now() - timedelta(days=7)
        recent = [n for n in notes if datetime.fromisoformat(n.created_at) >= recent_cut]
        by_cat: Dict[str, int] = {c: 0 for c in cats}
        for n in notes:
            by_cat[n.category] = by_cat.get(n.category, 0) + 1
        by_priority = {"high": 0, "medium": 0, "low": 0}
        for n in notes:
            by_priority[n.priority] += 1
        return {
            "total_notes": total,
            "total_categories": len(cats),
            "recent_notes": len(recent),
            "by_category": by_cat,
            "by_priority": by_priority,
        }


store = NotesStore(DATA_FILE)

############################################################
# مساعدات الواجهات
############################################################
CANCEL_BUTTON = "🚫 إلغاء"
BACK_BUTTON = "⬅️ رجوع"


def priority_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(PRIORITY_LABELS["high"], callback_data="prio:high"),
                InlineKeyboardButton(PRIORITY_LABELS["medium"], callback_data="prio:medium"),
                InlineKeyboardButton(PRIORITY_LABELS["low"], callback_data="prio:low"),
            ],
            [InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")],
        ]
    )


def quick_reminder_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏰ 30 دقيقة", callback_data="qrem:30m"),
                InlineKeyboardButton("⏰ 1 ساعة", callback_data="qrem:60m"),
            ],
            [
                InlineKeyboardButton("⏰ 2 ساعة", callback_data="qrem:120m"),
                InlineKeyboardButton("⏰ 6 ساعات", callback_data="qrem:360m"),
            ],
            [
                InlineKeyboardButton("📅 غداً 9ص", callback_data="qrem:tomorrow_9"),
                InlineKeyboardButton("📅 غداً 6م", callback_data="qrem:tomorrow_18"),
            ],
            [
                InlineKeyboardButton("🛠 وقت مخصص", callback_data="qrem:custom"),
                InlineKeyboardButton("🚫 بدون تذكير", callback_data="qrem:none"),
            ],
            [InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")],
        ]
    )


def days_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("اليوم", callback_data="cday:0"),
                InlineKeyboardButton("غداً", callback_data="cday:1"),
                InlineKeyboardButton("بعد غد", callback_data="cday:2"),
            ],
            [InlineKeyboardButton("الأسبوع القادم", callback_data="cday:7")],
            [InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")],
        ]
    )


def hour_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for start in range(0, 24, 6):
        row = []
        for h in range(start, start + 6):
            row.append(InlineKeyboardButton(f"{h:02d}", callback_data=f"chr:{h:02d}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")])
    return InlineKeyboardMarkup(rows)


def minute_group_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("00-09", callback_data="cmg:00"),
                InlineKeyboardButton("10-19", callback_data="cmg:10"),
                InlineKeyboardButton("20-29", callback_data="cmg:20"),
            ],
            [
                InlineKeyboardButton("30-39", callback_data="cmg:30"),
                InlineKeyboardButton("40-49", callback_data="cmg:40"),
                InlineKeyboardButton("50-59", callback_data="cmg:50"),
            ],
            [InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")],
        ]
    )


def minute_keyboard(group_start: int) -> InlineKeyboardMarkup:
    rows = []
    for start in range(group_start, group_start + 10, 5):
        row = []
        for m in range(start, start + 5):
            row.append(InlineKeyboardButton(f"{m:02d}", callback_data=f"cmin:{m:02d}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")])
    return InlineKeyboardMarkup(rows)


def paginate(items: List[str], page: int, per_page: int = 5) -> Tuple[List[str], int]:
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total_pages


def categories_keyboard(page: int = 1, action_prefix: str = "selcat:") -> InlineKeyboardMarkup:
    cats = store.list_categories()
    page_items, total_pages = paginate(cats, page)
    rows: List[List[InlineKeyboardButton]] = []
    for c in page_items:
        rows.append([InlineKeyboardButton(f"📁 {c}", callback_data=f"{action_prefix}{c}")])
    nav_row: List[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"nav:{action_prefix}{page-1}"))
    nav_row.append(InlineKeyboardButton(f"صفحة {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"nav:{action_prefix}{page+1}"))
    rows.append(nav_row)
    rows.append([InlineKeyboardButton("➕ تصنيف جديد", callback_data=f"{action_prefix}__new__")])
    rows.append([InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")])
    return InlineKeyboardMarkup(rows)


def notes_preview(note: Note) -> str:
    preview = note.body[:30] + ("..." if len(note.body) > 30 else "")
    prio = PRIORITY_LABELS.get(note.priority, "")
    return f"{prio.split()[0]} {note.title} - {preview}"


############################################################
# جدولة التذكيرات
############################################################
async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    job_data = context.job.data or {}
    user_id = job_data.get("user_id")
    note_id = job_data.get("note_id")
    note = store.get_note(note_id) if note_id else None
    if user_id and note:
        text = (
            f"⏰ تذكير بالملاحظة\n\n"
            f"{PRIORITY_LABELS[note.priority]}\n"
            f"🎯 {note.title}\n"
            f"📁 التصنيف: {note.category} | #ID: {note.note_id}\n\n"
            f"{note.body}"
        )
        try:
            await context.bot.send_message(chat_id=user_id, text=text)
        except Exception as e:
            logger.error(f"فشل إرسال التذكير: {e}")


def schedule_note_reminder(application: Application, user_id: int, note: Note) -> None:
    if not note.reminder_at:
        return
    try:
        when = datetime.fromisoformat(note.reminder_at)
        if when > datetime.now():
            job_name = f"note_rem_{note.note_id}"
            # إزالة أي مهمة سابقة لنفس الملاحظة
            for j in application.job_queue.get_jobs_by_name(job_name):
                j.schedule_removal()
            application.job_queue.run_once(
                send_reminder,
                when=when,
                chat_id=user_id,
                name=job_name,
                data={"user_id": user_id, "note_id": note.note_id},
            )
    except Exception as e:
        logger.error(f"خطأ في جدولة التذكير: {e}")


############################################################
# أوامر عامة: /start /menu /status /backup /stats /notes /search /edit /add
############################################################
async def send_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    menu_text = (
        "📋 قائمة الأوامر:\n\n"
        "1) /start - بدء وترحيب\n"
        "2) /add - إضافة ملاحظة أو تصنيف\n"
        "3) /notes - عرض الملاحظات\n"
        "4) /edit - تعديل\n"
        "5) /search - بحث متقدم\n"
        "6) /stats - إحصائيات\n"
        "7) /backup - نسخة احتياطية\n"
        "8) /menu - هذه القائمة\n\n"
        "نصائح: استخدم الأزرار للتنقل، وكل خطوة تحتوي زر إلغاء."
    )
    await update.effective_message.reply_text(menu_text)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = store.increment_test()
    welcome_text = (
        "🤖 مرحباً بك في بوت تنظيم الملاحظات!\n\n"
        "- بوت ذكي لتنظيم وإدارة الملاحظات بتصنيفات وتذكيرات وأولوية.\n"
        "- يدعم أزرار تفاعلية، نسخ احتياطي، وصفحات صحة.\n\n"
        "ابدأ بـ /add لإضافة أول ملاحظة، أو /menu لعرض الأوامر.\n\n"
        f"🔢 عداد الاختبارات: {count}\n"
    )
    await update.message.reply_text(welcome_text)
    await send_menu(update, context)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = store.data
    notes_count = len(store.get_notes())
    status_text = (
        "📊 حالة البوت:\n\n"
        "🟢 الحالة: نشط\n"
        f"📝 الملاحظات: {notes_count}\n"
        f"📁 التصنيفات: {len(store.list_categories())}\n"
        f"🔢 مرات الاختبار: {data.get('test_count', 0)}\n"
        f"⏰ آخر نشاط: {data.get('last_test', 'غير محدد')}\n"
        "🌐 الاستضافة: Render\n"
    )
    await update.message.reply_text(status_text)


async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"notes_backup_{ts}.txt"
    path = os.path.join(BACKUP_DIR, filename)
    os.makedirs(BACKUP_DIR, exist_ok=True)

    notes = store.get_notes()
    cats = store.list_categories()

    lines: List[str] = []
    lines.append(f"Backup created at: {datetime.now().isoformat()}")
    lines.append(f"Total notes: {len(notes)}")
    lines.append("")

    for cat in cats:
        cat_notes = [n for n in notes if n.category == cat]
        lines.append(f"=== {cat} ({len(cat_notes)}) ===")
        for n in sorted(cat_notes, key=lambda x: (PRIORITY_ORDER[x.priority], x.created_at)):
            lines.append(f"{PRIORITY_LABELS[n.priority]} | {n.title} | created: {n.created_at}")
            lines.append(f"#ID: {n.note_id}")
            if n.reminder_at:
                lines.append(f"Reminder: {n.reminder_at}")
            lines.append(n.body)
            lines.append("-")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    await update.message.reply_document(open(path, "rb"), filename=filename)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st = store.stats()
    pr = st["by_priority"]
    cats = st["by_category"]

    cat_lines = [f"- {c}: {num}" for c, num in cats.items()]
    text = (
        "📊 إحصائيات:\n\n"
        f"إجمالي الملاحظات: {st['total_notes']}\n"
        f"إجمالي التصنيفات: {st['total_categories']}\n"
        f"الملاحظات الحديثة (7 أيام): {st['recent_notes']}\n\n"
        f"توزيع الأولويات:\n"
        f"🔴 high: {pr['high']} | 🟡 medium: {pr['medium']} | 🟢 low: {pr['low']}\n\n"
        f"تفصيل التصنيفات:\n" + "\n".join(cat_lines)
    )
    await update.message.reply_text(text)


async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes = store.get_notes()
    cats = store.list_categories()
    if not notes:
        await update.message.reply_text("لا توجد ملاحظات بعد. استخدم /add لإضافة ملاحظة.")
        return
    lines: List[str] = []
    for cat in cats:
        cat_notes = [n for n in notes if n.category == cat]
        if not cat_notes:
            continue
        lines.append(f"📁 {cat} ({len(cat_notes)})")
        for n in sorted(cat_notes, key=lambda x: (PRIORITY_ORDER[x.priority], x.created_at))[:5]:
            lines.append(f"{notes_preview(n)}")
        extra = len(cat_notes) - 5
        if extra > 0:
            lines.append(f"(+{extra}) ملاحظات إضافية")
        lines.append("")
    await update.message.reply_text("\n".join(lines).strip())


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("استخدم: /search كلمة_بحث")
        return
    q = query.strip().lower()
    results = []
    for n in store.get_notes():
        if (
            q in n.title.lower()
            or q in n.body.lower()
            or q in n.category.lower()
        ):
            results.append(n)
    results = results[:10]
    if not results:
        await update.message.reply_text("لا توجد نتائج")
        return
    lines = [f"نتائج ({len(results)}):"]
    for i, n in enumerate(results, start=1):
        lines.append(
            f"{i}. {notes_preview(n)}\n📁 {n.category} | #ID: {n.note_id}"
        )
    await update.message.reply_text("\n\n".join(lines))


############################################################
# محادثة /add
############################################################
(
    ADD_CHOOSE_TYPE,
    ADD_NOTE_CATEGORY,
    ADD_NOTE_TITLE,
    ADD_NOTE_BODY,
    ADD_NOTE_PRIORITY,
    ADD_NOTE_REMINDER_TYPE,
    ADD_NOTE_QUICK_OR_CUSTOM,
    ADD_NOTE_CUSTOM_DAY,
    ADD_NOTE_CUSTOM_HOUR,
    ADD_NOTE_CUSTOM_MIN_GROUP,
    ADD_NOTE_CUSTOM_MIN,
    ADD_CATEGORY_NAME,
) = range(12)


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📝 ملاحظة", callback_data="add:type:note"),
                InlineKeyboardButton("📁 تصنيف", callback_data="add:type:cat"),
            ],
            [InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")],
        ]
    )
    await update.message.reply_text("ماذا تريد إضافة؟", reply_markup=kb)
    return ADD_CHOOSE_TYPE


async def add_choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if q.data == "add:type:note":
        await q.edit_message_text("اختر التصنيف:", reply_markup=categories_keyboard(1, "addsel:") )
        return ADD_NOTE_CATEGORY
    elif q.data == "add:type:cat":
        await q.edit_message_text("أدخل اسم التصنيف الجديد:")
        return ADD_CATEGORY_NAME
    return ADD_CHOOSE_TYPE


async def add_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data.startswith("nav:addsel:"):
        try:
            new_page = int(data.split(":")[-1])
        except Exception:
            new_page = 1
        await q.edit_message_reply_markup(reply_markup=categories_keyboard(new_page, "addsel:"))
        return ADD_NOTE_CATEGORY
    if data.startswith("addsel:"):
        cat = data.split(":", 1)[1]
        if cat == "__new__":
            await q.edit_message_text("أدخل اسم التصنيف الجديد:")
            return ADD_CATEGORY_NAME
        context.user_data["add_category"] = cat
        await q.edit_message_text(f"التصنيف المختار: {cat}\n\nاكتب عنوان الملاحظة:")
        return ADD_NOTE_TITLE
    return ADD_NOTE_CATEGORY


async def add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("يرجى إدخال اسم صالح.")
        return ADD_CATEGORY_NAME
    store.add_category(name)
    # تحقّق هل نحن في تدفق إضافة الملاحظة
    if context.user_data.get("add_category") is None and context.user_data.get("add_flow_started") is None:
        await update.message.reply_text(f"تمت إضافة التصنيف: {name}")
        return ConversationHandler.END
    # وإلا نكمل تدفق إضافة الملاحظة بهذا التصنيف
    context.user_data["add_category"] = name
    await update.message.reply_text(f"التصنيف المختار: {name}\n\nاكتب عنوان الملاحظة:")
    return ADD_NOTE_TITLE


async def add_note_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("يرجى إدخال عنوان صالح.")
        return ADD_NOTE_TITLE
    context.user_data["add_title"] = title
    await update.message.reply_text("اكتب نص الملاحظة:")
    return ADD_NOTE_BODY


async def add_note_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    body = update.message.text.strip()
    if not body:
        await update.message.reply_text("يرجى إدخال نص صالح.")
        return ADD_NOTE_BODY
    context.user_data["add_body"] = body
    await update.message.reply_text(
        "اختر الأولوية:", reply_markup=priority_keyboard()
    )
    return ADD_NOTE_PRIORITY


async def add_note_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if q.data.startswith("prio:"):
        priority = q.data.split(":")[1]
        context.user_data["add_priority"] = priority
        await q.edit_message_text(
            "اختر نوع التذكير:", reply_markup=quick_reminder_keyboard()
        )
        return ADD_NOTE_REMINDER_TYPE
    return ADD_NOTE_PRIORITY


async def add_note_reminder_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END

    data = q.data
    if data.startswith("qrem:"):
        opt = data.split(":")[1]
        context.user_data["add_reminder_type"] = opt
        if opt == "none":
            # إنشاء الملاحظة دون تذكير
            note = store.add_note(
                category=context.user_data["add_category"],
                title=context.user_data["add_title"],
                body=context.user_data["add_body"],
                priority=context.user_data["add_priority"],
                reminder_at=None,
            )
            await q.edit_message_text(
                f"✅ تمت إضافة الملاحظة\n{notes_preview(note)}\n📁 {note.category} | #ID: {note.note_id}"
            )
            return ConversationHandler.END
        elif opt == "custom":
            await q.edit_message_text(
                "اختَر اليوم:", reply_markup=days_keyboard()
            )
            return ADD_NOTE_CUSTOM_DAY
        else:
            # خيارات سريعة بالنسبة للدقائق/غداً
            now = datetime.now()
            when: Optional[datetime] = None
            if opt.endswith("m"):
                delta_m = int(opt[:-1])
                when = now + timedelta(minutes=delta_m)
            elif opt == "tomorrow_9":
                when = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            elif opt == "tomorrow_18":
                when = (now + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
            note = store.add_note(
                category=context.user_data["add_category"],
                title=context.user_data["add_title"],
                body=context.user_data["add_body"],
                priority=context.user_data["add_priority"],
                reminder_at=when,
            )
            if when:
                schedule_note_reminder(context.application, update.effective_user.id, note)
            await q.edit_message_text(
                f"✅ تمت إضافة الملاحظة مع تذكير\n⏰ {when.strftime('%Y-%m-%d %H:%M')}\n{notes_preview(note)}\n📁 {note.category} | #ID: {note.note_id}"
            )
            return ConversationHandler.END
    return ADD_NOTE_REMINDER_TYPE


async def add_note_custom_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if q.data.startswith("cday:"):
        days = int(q.data.split(":")[1])
        context.user_data["add_custom_days"] = days
        await q.edit_message_text("اختر الساعة:", reply_markup=hour_keyboard())
        return ADD_NOTE_CUSTOM_HOUR
    return ADD_NOTE_CUSTOM_DAY


async def add_note_custom_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if q.data.startswith("chr:"):
        hour = int(q.data.split(":")[1])
        context.user_data["add_custom_hour"] = hour
        await q.edit_message_text(
            "اختر مجموعة الدقائق:", reply_markup=minute_group_keyboard()
        )
        return ADD_NOTE_CUSTOM_MIN_GROUP
    return ADD_NOTE_CUSTOM_HOUR


async def add_note_custom_min_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if q.data.startswith("cmg:"):
        mg = int(q.data.split(":")[1])
        context.user_data["add_custom_min_group"] = mg
        await q.edit_message_text(
            "اختر الدقيقة الدقيقة:", reply_markup=minute_keyboard(mg)
        )
        return ADD_NOTE_CUSTOM_MIN
    return ADD_NOTE_CUSTOM_MIN_GROUP


async def add_note_custom_min(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if q.data.startswith("cmin:"):
        minute = int(q.data.split(":")[1])
        days = int(context.user_data.get("add_custom_days", 0))
        hour = int(context.user_data.get("add_custom_hour", 0))
        now = datetime.now()
        when = (now + timedelta(days=days)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        note = store.add_note(
            category=context.user_data["add_category"],
            title=context.user_data["add_title"],
            body=context.user_data["add_body"],
            priority=context.user_data["add_priority"],
            reminder_at=when,
        )
        schedule_note_reminder(context.application, update.effective_user.id, note)
        await q.edit_message_text(
            f"✅ تمت إضافة الملاحظة مع تذكير\n⏰ {when.strftime('%Y-%m-%d %H:%M')}\n{notes_preview(note)}\n📁 {note.category} | #ID: {note.note_id}"
        )
        return ConversationHandler.END
    return ADD_NOTE_CUSTOM_MIN


############################################################
# محادثة /edit
############################################################
(
    EDIT_CHOOSE_TYPE,
    EDIT_CATEGORY_PICK,
    EDIT_CATEGORY_ACTION,
    EDIT_CATEGORY_RENAME,
    EDIT_NOTE_PICK,
    EDIT_NOTE_ACTION,
    EDIT_NOTE_TITLE,
    EDIT_NOTE_BODY,
    EDIT_NOTE_PRIORITY,
    EDIT_NOTE_REMINDER,
) = range(12, 22)


def notes_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    notes = store.get_notes()
    notes_sorted = sorted(notes, key=lambda n: (n.category, PRIORITY_ORDER[n.priority], n.created_at))
    page_items, total_pages = paginate(notes_sorted, page)
    rows: List[List[InlineKeyboardButton]] = []
    for n in page_items:
        rows.append([
            InlineKeyboardButton(notes_preview(n), callback_data=f"enote:{n.note_id}")
        ])
    nav_row: List[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"nav:enote:{page-1}"))
    nav_row.append(InlineKeyboardButton(f"صفحة {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"nav:enote:{page+1}"))
    rows.append(nav_row)
    rows.append([InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")])
    return InlineKeyboardMarkup(rows)


async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📁 تعديل تصنيف", callback_data="edit:type:cat"),
                InlineKeyboardButton("📝 تعديل ملاحظة", callback_data="edit:type:note"),
            ],
            [InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")],
        ]
    )
    await update.message.reply_text("اختر ما تريد تعديله:", reply_markup=kb)
    return EDIT_CHOOSE_TYPE


async def edit_choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if q.data == "edit:type:cat":
        await q.edit_message_text(
            "اختر تصنيف:", reply_markup=categories_keyboard(1, "ecat:")
        )
        return EDIT_CATEGORY_PICK
    if q.data == "edit:type:note":
        await q.edit_message_text(
            "اختر ملاحظة:", reply_markup=notes_keyboard(1)
        )
        return EDIT_NOTE_PICK
    return EDIT_CHOOSE_TYPE


async def edit_category_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if q.data.startswith("nav:ecat:"):
        page = int(q.data.split(":")[-1])
        await q.edit_message_reply_markup(reply_markup=categories_keyboard(page, "ecat:"))
        return EDIT_CATEGORY_PICK
    if q.data.startswith("ecat:"):
        cat = q.data.split(":", 1)[1]
        if cat == "__new__":
            await q.edit_message_text("أدخل اسم التصنيف الجديد:")
            return EDIT_CATEGORY_RENAME  # سنُعيد استخدامه للإضافة إذا لزم
        context.user_data["edit_category"] = cat
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✏️ تعديل الاسم", callback_data="ecata:rename"),
                    InlineKeyboardButton("🗑 حذف", callback_data="ecata:delete"),
                ],
                [InlineKeyboardButton(BACK_BUTTON, callback_data="ecata:back")],
                [InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")],
            ]
        )
        await q.edit_message_text(f"التصنيف: {cat}\nاختر إجراء:", reply_markup=kb)
        return EDIT_CATEGORY_ACTION
    return EDIT_CATEGORY_PICK


async def edit_category_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    cat = context.user_data.get("edit_category")
    if data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "ecata:back":
        await q.edit_message_text(
            "اختر تصنيف:", reply_markup=categories_keyboard(1, "ecat:")
        )
        return EDIT_CATEGORY_PICK
    if data == "ecata:rename":
        await q.edit_message_text("أدخل الاسم الجديد:")
        return EDIT_CATEGORY_RENAME
    if data == "ecata:delete":
        if cat == "عام":
            await q.edit_message_text("لا يمكن حذف التصنيف الافتراضي 'عام'.")
            return EDIT_CATEGORY_ACTION
        ok = store.delete_category(cat)
        if ok:
            await q.edit_message_text("تم حذف التصنيف ونقل ملاحظاته إلى 'عام'.")
        else:
            await q.edit_message_text("تعذر حذف التصنيف.")
        return ConversationHandler.END
    return EDIT_CATEGORY_ACTION


async def edit_category_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text.strip()
    if not new_name:
        await update.message.reply_text("يرجى إدخال اسم صالح.")
        return EDIT_CATEGORY_RENAME
    cat = context.user_data.get("edit_category")
    if cat:
        ok = store.rename_category(cat, new_name)
        if ok:
            await update.message.reply_text("تم تغيير الاسم بنجاح.")
        else:
            await update.message.reply_text("تعذر تغيير الاسم (قد يكون موجوداً).")
    else:
        # إضافة جديدة (في حالة came from __new__)
        store.add_category(new_name)
        await update.message.reply_text("تمت إضافة التصنيف.")
    return ConversationHandler.END


async def edit_note_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data.startswith("nav:enote:"):
        page = int(data.split(":")[-1])
        await q.edit_message_reply_markup(reply_markup=notes_keyboard(page))
        return EDIT_NOTE_PICK
    if data.startswith("enote:"):
        note_id = int(data.split(":")[1])
        context.user_data["edit_note_id"] = note_id
        note = store.get_note(note_id)
        if not note:
            await q.edit_message_text("لم يتم العثور على الملاحظة.")
            return ConversationHandler.END
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✏️ العنوان", callback_data="eact:title"),
                    InlineKeyboardButton("📝 النص", callback_data="eact:body"),
                ],
                [
                    InlineKeyboardButton("🎯 الأولوية", callback_data="eact:prio"),
                    InlineKeyboardButton("⏰ التذكير", callback_data="eact:rem"),
                ],
                [InlineKeyboardButton("🗑 حذف", callback_data="eact:del")],
                [InlineKeyboardButton(BACK_BUTTON, callback_data="eact:back")],
                [InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")],
            ]
        )
        preview = (
            f"معاينة:\n{notes_preview(note)}\n📁 {note.category} | #ID: {note.note_id}"
        )
        await q.edit_message_text(preview + "\nاختر إجراء:", reply_markup=kb)
        return EDIT_NOTE_ACTION
    return EDIT_NOTE_PICK


async def edit_note_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if data == "eact:back":
        await q.edit_message_text("اختر ملاحظة:", reply_markup=notes_keyboard(1))
        return EDIT_NOTE_PICK

    note_id = context.user_data.get("edit_note_id")
    note = store.get_note(note_id) if note_id else None
    if not note:
        await q.edit_message_text("لم يتم العثور على الملاحظة.")
        return ConversationHandler.END

    if data == "eact:title":
        await q.edit_message_text("أرسل العنوان الجديد:")
        return EDIT_NOTE_TITLE
    if data == "eact:body":
        await q.edit_message_text("أرسل النص الجديد:")
        return EDIT_NOTE_BODY
    if data == "eact:prio":
        await q.edit_message_text("اختر أولوية:", reply_markup=priority_keyboard())
        return EDIT_NOTE_PRIORITY
    if data == "eact:rem":
        await q.edit_message_text(
            "اختر نوع التذكير:", reply_markup=quick_reminder_keyboard()
        )
        return EDIT_NOTE_REMINDER
    if data == "eact:del":
        ok = store.delete_note(note.note_id)
        if ok:
            await q.edit_message_text("تم حذف الملاحظة.")
        else:
            await q.edit_message_text("تعذر حذف الملاحظة.")
        return ConversationHandler.END
    return EDIT_NOTE_ACTION


async def edit_note_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    note_id = context.user_data.get("edit_note_id")
    note = store.get_note(note_id) if note_id else None
    if not note:
        await update.message.reply_text("لم يتم العثور على الملاحظة.")
        return ConversationHandler.END
    note.title = text
    store.update_note(note)
    await update.message.reply_text("تم تحديث العنوان.")
    return ConversationHandler.END


async def edit_note_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    note_id = context.user_data.get("edit_note_id")
    note = store.get_note(note_id) if note_id else None
    if not note:
        await update.message.reply_text("لم يتم العثور على الملاحظة.")
        return ConversationHandler.END
    note.body = text
    store.update_note(note)
    await update.message.reply_text("تم تحديث النص.")
    return ConversationHandler.END


async def edit_note_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    if q.data.startswith("prio:"):
        pr = q.data.split(":")[1]
        note_id = context.user_data.get("edit_note_id")
        note = store.get_note(note_id) if note_id else None
        if not note:
            await q.edit_message_text("لم يتم العثور على الملاحظة.")
            return ConversationHandler.END
        note.priority = pr
        store.update_note(note)
        await q.edit_message_text("تم تحديث الأولوية.")
        return ConversationHandler.END
    return EDIT_NOTE_PRIORITY


async def edit_note_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel":
        await q.edit_message_text("تم الإلغاء.")
        return ConversationHandler.END
    note_id = context.user_data.get("edit_note_id")
    note = store.get_note(note_id) if note_id else None
    if not note:
        await q.edit_message_text("لم يتم العثور على الملاحظة.")
        return ConversationHandler.END

    data = q.data
    if data.startswith("qrem:"):
        opt = data.split(":")[1]
        now = datetime.now()
        when: Optional[datetime] = None
        if opt == "none":
            note.reminder_at = None
            store.update_note(note)
            await q.edit_message_text("تم إزالة التذكير.")
            return ConversationHandler.END
        if opt == "custom":
            await q.edit_message_text("اختَر اليوم:", reply_markup=days_keyboard())
            # إعادة استخدام نفس حالة الإضافة المخصصة عبر مفاتيح user_data المؤقتة
            context.user_data["_edit_rem_for_note"] = note.note_id
            return ADD_NOTE_CUSTOM_DAY
        if opt.endswith("m"):
            delta_m = int(opt[:-1])
            when = now + timedelta(minutes=delta_m)
        elif opt == "tomorrow_9":
            when = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        elif opt == "tomorrow_18":
            when = (now + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)

        if when:
            note.reminder_at = when.isoformat()
            store.update_note(note)
            schedule_note_reminder(context.application, update.effective_user.id, note)
            await q.edit_message_text(f"تم تحديث التذكير إلى {when.strftime('%Y-%m-%d %H:%M')}")
            return ConversationHandler.END
    return EDIT_NOTE_REMINDER


############################################################
# إلغاء عام
############################################################
async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


############################################################
# خادم الويب لصفحات الصحة
############################################################
class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):  # type: ignore[override]
        if self.path == "/" or self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            stats = store.stats()
            response = f"""
            <html>
            <head><title>Notes Bot</title></head>
            <body>
                <h1>🤖 بوت الملاحظات يعمل!</h1>
                <p>✅ البوت نشط</p>
                <p>📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>📝 إجمالي الملاحظات: {stats.get('total_notes', 0)}</p>
                <p>📁 التصنيفات: {stats.get('total_categories', 0)}</p>
            </body>
            </html>
            """.encode("utf-8")
            self.wfile.write(response)
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            health_data = {
                "status": "healthy",
                "bot": "running",
                "timestamp": datetime.now().isoformat(),
                "notes": len(store.get_notes()),
            }
            self.wfile.write(json.dumps(health_data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>404 - Page Not Found</h1>")


def start_web_server() -> None:
    try:
        with socketserver.TCPServer(("", WEB_PORT), SimpleHTTPRequestHandler) as httpd:
            logger.info(f"🌐 خادم الويب يعمل على المنفذ {WEB_PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"خطأ في خادم الويب: {e}")


############################################################
# main
############################################################
async def post_startup_jobs(app: Application) -> None:
    # إعادة جدولة التذكيرات المستقبلية عند التشغيل
    # ملاحظة: نربط كل التذكيرات بمُستخدم يرسل /start أولاً؛ هنا لا نعلم المستخدمين.
    # سنقوم بجدولة عند إضافة/تعديل الملاحظة فقط. يمكن توسيعها بتخزين user_id لكل ملاحظة.
    pass


def build_application() -> Application:
    application = Application.builder().token(BOT_TOKEN).build()

    # /menu
    application.add_handler(CommandHandler("menu", send_menu))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("backup", backup_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("notes", notes_command))
    application.add_handler(CommandHandler("search", search_command))

    # /add conversation
    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_command)],
        states={
            ADD_CHOOSE_TYPE: [CallbackQueryHandler(add_choose_type)],
            ADD_NOTE_CATEGORY: [CallbackQueryHandler(add_select_category)],
            ADD_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name)],
            ADD_NOTE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_note_title)],
            ADD_NOTE_BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_note_body)],
            ADD_NOTE_PRIORITY: [CallbackQueryHandler(add_note_priority)],
            ADD_NOTE_REMINDER_TYPE: [CallbackQueryHandler(add_note_reminder_type)],
            ADD_NOTE_CUSTOM_DAY: [CallbackQueryHandler(add_note_custom_day)],
            ADD_NOTE_CUSTOM_HOUR: [CallbackQueryHandler(add_note_custom_hour)],
            ADD_NOTE_CUSTOM_MIN_GROUP: [CallbackQueryHandler(add_note_custom_min_group)],
            ADD_NOTE_CUSTOM_MIN: [CallbackQueryHandler(add_note_custom_min)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        name="add_conv",
        persistent=False,
    )
    application.add_handler(add_conv)

    # /edit conversation
    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_command)],
        states={
            EDIT_CHOOSE_TYPE: [CallbackQueryHandler(edit_choose_type)],
            EDIT_CATEGORY_PICK: [CallbackQueryHandler(edit_category_pick)],
            EDIT_CATEGORY_ACTION: [CallbackQueryHandler(edit_category_action)],
            EDIT_CATEGORY_RENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_category_rename)],
            EDIT_NOTE_PICK: [CallbackQueryHandler(edit_note_pick)],
            EDIT_NOTE_ACTION: [CallbackQueryHandler(edit_note_action)],
            EDIT_NOTE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_note_title)],
            EDIT_NOTE_BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_note_body)],
            EDIT_NOTE_PRIORITY: [CallbackQueryHandler(edit_note_priority)],
            EDIT_NOTE_REMINDER: [CallbackQueryHandler(edit_note_reminder)],
            # ملاحظة: لإعداد وقت مخصص من مسار التعديل، نعيد استخدام حالات الإضافة:
            ADD_NOTE_CUSTOM_DAY: [CallbackQueryHandler(add_note_custom_day)],
            ADD_NOTE_CUSTOM_HOUR: [CallbackQueryHandler(add_note_custom_hour)],
            ADD_NOTE_CUSTOM_MIN_GROUP: [CallbackQueryHandler(add_note_custom_min_group)],
            ADD_NOTE_CUSTOM_MIN: [CallbackQueryHandler(add_note_custom_min)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        name="edit_conv",
        persistent=False,
    )
    application.add_handler(edit_conv)

    return application


def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN غير مُعرّف في المتغيرات البيئية.")
        return

    application = build_application()

    # تشغيل خادم الويب في خيط منفصل
    web_server_thread = threading.Thread(target=start_web_server, daemon=True)
    web_server_thread.start()

    logger.info("🤖 بوت الملاحظات يعمل الآن...")
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
