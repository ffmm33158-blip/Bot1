from typing import List, Tuple, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def chunk_list(items: List, size: int) -> List[List]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def build_category_keyboard(categories: List[Tuple[str, str]], include_add: bool = True) -> InlineKeyboardMarkup:
    buttons: List[List[InlineKeyboardButton]] = []
    for cid, name in categories:
        buttons.append([InlineKeyboardButton(f"📁 {name}", callback_data=f"cat:{cid}")])
    if include_add:
        buttons.append([InlineKeyboardButton("➕ إضافة تصنيف جديد", callback_data="cat_add:new")])
    buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def build_priority_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("🔴 مهم جداً", callback_data="prio:red"),
            InlineKeyboardButton("🟡 مهم", callback_data="prio:yellow"),
            InlineKeyboardButton("🟢 عادي", callback_data="prio:green"),
        ],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(buttons)


def build_reminder_quick_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("⏰ 30 د", callback_data="rem:rel:30min"),
            InlineKeyboardButton("1 س", callback_data="rem:rel:1h"),
            InlineKeyboardButton("2 س", callback_data="rem:rel:2h"),
            InlineKeyboardButton("6 س", callback_data="rem:rel:6h"),
        ],
        [
            InlineKeyboardButton("📅 غداً 9 ص", callback_data="rem:abs:tomorrow_09"),
            InlineKeyboardButton("غداً 6 م", callback_data="rem:abs:tomorrow_18"),
        ],
        [
            InlineKeyboardButton("🕒 وقت مخصص", callback_data="rem:custom"),
            InlineKeyboardButton("🚫 بدون تذكير", callback_data="rem:none"),
        ],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(buttons)


def build_pagination_keyboard(page: int, page_count: int, base: str) -> InlineKeyboardMarkup:
    buttons: List[InlineKeyboardButton] = []
    if page > 1:
        buttons.append(InlineKeyboardButton("◀️ السابق", callback_data=f"{base}:page:{page-1}"))
    if page < page_count:
        buttons.append(InlineKeyboardButton("التالي ▶️", callback_data=f"{base}:page:{page+1}"))
    rows = [buttons] if buttons else []
    rows.append([InlineKeyboardButton("❌ إغلاق", callback_data="close")])
    return InlineKeyboardMarkup(rows)


def build_yes_no_keyboard(base: str = "yn") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ نعم", callback_data=f"{base}:yes"),
                InlineKeyboardButton("❌ لا", callback_data=f"{base}:no"),
            ]
        ]
    )