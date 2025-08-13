from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class Priority(str, Enum):
    critical = "red"   # 🔴
    important = "yellow"  # 🟡
    normal = "green"   # 🟢


@dataclass
class Reminder:
    type: str  # none|relative|absolute
    at_iso: Optional[str] = None  # ISO timestamp in UTC
    scheduled: bool = False
    job_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "at_iso": self.at_iso,
            "scheduled": self.scheduled,
            "job_id": self.job_id,
        }


@dataclass
class Note:
    id: int
    category_id: str
    title: str
    text: str
    priority: Priority
    created_at: str  # ISO timestamp in UTC
    reminder: Reminder = field(default_factory=lambda: Reminder(type="none"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category_id": self.category_id,
            "title": self.title,
            "text": self.text,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "reminder": self.reminder.to_dict(),
        }


@dataclass
class Category:
    id: str
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name}