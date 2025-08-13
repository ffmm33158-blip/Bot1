from datetime import datetime
from typing import Optional, List, Dict, Any
import json
from config import TIMEZONE, PRIORITY_COLORS

class Note:
    """نموذج بيانات الملاحظة"""
    
    def __init__(self, title: str, content: str, category: str, priority: str = 'low', 
                 note_id: Optional[int] = None, created_at: Optional[datetime] = None,
                 reminder_time: Optional[datetime] = None):
        self.id = note_id or int(datetime.now().timestamp() * 1000)
        self.title = title
        self.content = content
        self.category = category
        self.priority = priority
        self.created_at = created_at or datetime.now(TIMEZONE)
        self.reminder_time = reminder_time
        self.is_reminded = False
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل الملاحظة إلى قاموس"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
            'is_reminded': self.is_reminded
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Note':
        """إنشاء ملاحظة من قاموس"""
        note = cls(
            title=data['title'],
            content=data['content'],
            category=data['category'],
            priority=data.get('priority', 'low'),
            note_id=data['id']
        )
        
        if data.get('created_at'):
            note.created_at = datetime.fromisoformat(data['created_at'])
        
        if data.get('reminder_time'):
            note.reminder_time = datetime.fromisoformat(data['reminder_time'])
            
        note.is_reminded = data.get('is_reminded', False)
        return note
    
    def get_priority_emoji(self) -> str:
        """الحصول على رمز الأولوية"""
        return PRIORITY_COLORS.get(self.priority, PRIORITY_COLORS['low'])['emoji']
    
    def get_priority_text(self) -> str:
        """الحصول على نص الأولوية"""
        return PRIORITY_COLORS.get(self.priority, PRIORITY_COLORS['low'])['text']
    
    def get_preview(self, max_length: int = 30) -> str:
        """الحصول على معاينة النص"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
    
    def format_for_display(self, show_category: bool = True, show_id: bool = True) -> str:
        """تنسيق الملاحظة للعرض"""
        emoji = self.get_priority_emoji()
        preview = self.get_preview()
        
        display_text = f"{emoji} {self.title}"
        if preview and preview != self.title:
            display_text += f" - {preview}"
        
        if show_category or show_id:
            footer_parts = []
            if show_category:
                footer_parts.append(f"📁 التصنيف: {self.category}")
            if show_id:
                footer_parts.append(f"#ID: {self.id}")
            
            if footer_parts:
                display_text += f"\n{' | '.join(footer_parts)}"
        
        return display_text

class Category:
    """نموذج بيانات التصنيف"""
    
    def __init__(self, name: str, created_at: Optional[datetime] = None):
        self.name = name
        self.created_at = created_at or datetime.now(TIMEZONE)
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل التصنيف إلى قاموس"""
        return {
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Category':
        """إنشاء تصنيف من قاموس"""
        category = cls(name=data['name'])
        
        if data.get('created_at'):
            category.created_at = datetime.fromisoformat(data['created_at'])
        
        return category

class UserSession:
    """نموذج جلسة المستخدم لتتبع الحالة"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.current_action = None
        self.temp_data = {}
        self.step = 0
        self.last_activity = datetime.now(TIMEZONE)
    
    def reset(self):
        """إعادة تعيين الجلسة"""
        self.current_action = None
        self.temp_data = {}
        self.step = 0
        self.last_activity = datetime.now(TIMEZONE)
    
    def set_action(self, action: str, **kwargs):
        """تعيين إجراء جديد"""
        self.current_action = action
        self.temp_data = kwargs
        self.step = 0
        self.last_activity = datetime.now(TIMEZONE)
    
    def next_step(self):
        """الانتقال للخطوة التالية"""
        self.step += 1
        self.last_activity = datetime.now(TIMEZONE)
    
    def update_temp_data(self, **kwargs):
        """تحديث البيانات المؤقتة"""
        self.temp_data.update(kwargs)
        self.last_activity = datetime.now(TIMEZONE)