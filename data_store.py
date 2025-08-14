import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

class DataStore:
    def __init__(self, filename: str = "data.json"):
        self.filename = filename
        
    def _read(self) -> Dict[str, Any]:
        if not os.path.exists(self.filename):
            return {"users": {}}
        
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"users": {}}
    
    def _write(self, data: Dict[str, Any]) -> None:
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_user(self, user_id: str) -> None:
        data = self._read()
        if user_id not in data["users"]:
            data["users"][user_id] = {
                "notes": [],
                "created_at": datetime.now().isoformat()
            }
            self._write(data)
    
    def add_note(self, user_id: str, title: str, text: str, priority: str = "green", reminder: Optional[str] = None) -> int:
        data = self._read()
        if user_id not in data["users"]:
            self.add_user(user_id)
        
        note_id = len(data["users"][user_id]["notes"]) + 1
        note = {
            "id": note_id,
            "title": title,
            "text": text,
            "priority": priority,
            "reminder": reminder,
            "created_at": datetime.now().isoformat()
        }
        
        data["users"][user_id]["notes"].append(note)
        self._write(data)
        return note_id
    
    def get_note(self, user_id: str, note_id: int) -> Optional[Dict[str, Any]]:
        data = self._read()
        if user_id not in data["users"]:
            return None
        
        for note in data["users"][user_id]["notes"]:
            if note["id"] == note_id:
                return note
        return None
    
    def get_user_notes(self, user_id: str) -> List[Dict[str, Any]]:
        data = self._read()
        if user_id not in data["users"]:
            return []
        return data["users"][user_id]["notes"]
    
    def delete_note(self, user_id: str, note_id: int) -> bool:
        data = self._read()
        if user_id not in data["users"]:
            return False
        
        for i, note in enumerate(data["users"][user_id]["notes"]):
            if note["id"] == note_id:
                del data["users"][user_id]["notes"][i]
                self._write(data)
                return True
        return False
    
    def edit_note(self, user_id: str, note_id: int, title: str = None, text: str = None, priority: str = None) -> bool:
        data = self._read()
        if user_id not in data["users"]:
            return False
        
        for note in data["users"][user_id]["notes"]:
            if note["id"] == note_id:
                if title is not None:
                    note["title"] = title
                if text is not None:
                    note["text"] = text
                if priority is not None:
                    note["priority"] = priority
                note["updated_at"] = datetime.now().isoformat()
                self._write(data)
                return True
        return False
