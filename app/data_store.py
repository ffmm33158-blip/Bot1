import json
import os
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from filelock import FileLock

DEFAULT_CATEGORIES = [
    {"id": "general", "name": "عام"},
    {"id": "tasks", "name": "مهام"},
    {"id": "ideas", "name": "أفكار"},
]


class DataStore:
    def __init__(self, base_dir: str = "data", filename: str = "notes.json") -> None:
        self.base_dir = base_dir
        self.file_path = os.path.join(base_dir, filename)
        self.backup_dir = os.path.join(base_dir, "backups")
        self.lock_path = f"{self.file_path}.lock"
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        if not os.path.exists(self.file_path):
            self._write({"users": {}})

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _read(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            return {"users": {}}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            latest_backup = self._find_latest_backup()
            if latest_backup:
                with open(latest_backup, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {"users": {}}

    def _write(self, data: Dict[str, Any]) -> None:
        lock = FileLock(self.lock_path)
        with lock:
            tmp_path = f"{self.file_path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.file_path)
            self._auto_backup()

    def _auto_backup(self) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"notes_auto_{ts}.json")
        try:
            shutil.copy2(self.file_path, backup_path)
        except Exception:
            pass

    def _find_latest_backup(self) -> Optional[str]:
        backups = [
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.startswith("notes_auto_") and f.endswith(".json")
        ]
        if not backups:
            return None
        backups.sort()
        return backups[-1]

    def _ensure_user(self, user_id: str) -> Dict[str, Any]:
        data = self._read()
        users = data.setdefault("users", {})
        if user_id not in users:
            users[user_id] = {
                "categories": DEFAULT_CATEGORIES.copy(),
                "notes": [],
                "next_note_id": 1,
            }
            self._write(data)
        return users[user_id]

    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        data = self._read()
        return data.get("users", {}).get(user_id, {
            "categories": DEFAULT_CATEGORIES.copy(),
            "notes": [],
            "next_note_id": 1,
        })

    def add_category(self, user_id: str, name: str) -> Dict[str, Any]:
        data = self._read()
        user = self._ensure_user(user_id)
        slug = self._slugify_category(name, user["categories"])  # unique id
        user["categories"].append({"id": slug, "name": name})
        data["users"][user_id] = user
        self._write(data)
        return {"id": slug, "name": name}

    def _slugify_category(self, name: str, existing: List[Dict[str, Any]]) -> str:
        base = self._to_slug(name)
        slug = base
        i = 2
        existing_ids = {c["id"] for c in existing}
        while slug in existing_ids:
            slug = f"{base}-{i}"
            i += 1
        return slug

    def _to_slug(self, s: str) -> str:
        s = s.strip().lower()
        s = s.replace(" ", "-")
        return "".join(ch for ch in s if ch.isalnum() or ch == '-') or "cat"

    def list_categories(self, user_id: str) -> List[Dict[str, Any]]:
        return self._ensure_user(user_id)["categories"]

    def rename_category(self, user_id: str, category_id: str, new_name: str) -> bool:
        data = self._read()
        user = self._ensure_user(user_id)
        for c in user["categories"]:
            if c["id"] == category_id:
                c["name"] = new_name
                self._write(data)
                return True
        return False

    def delete_category(self, user_id: str, category_id: str) -> bool:
        data = self._read()
        user = self._ensure_user(user_id)
        if category_id == "general":
            return False
        user["categories"] = [c for c in user["categories"] if c["id"] != category_id]
        for n in user["notes"]:
            if n["category_id"] == category_id:
                n["category_id"] = "general"
        self._write(data)
        return True

    def add_note(self, user_id: str, category_id: str, title: str, text: str, priority: str, reminder: Dict[str, Any]) -> int:
        data = self._read()
        user = self._ensure_user(user_id)
        note_id = int(user.get("next_note_id", 1))
        user["next_note_id"] = note_id + 1
        note = {
            "id": note_id,
            "category_id": category_id,
            "title": title,
            "text": text,
            "priority": priority,
            "created_at": self._now_iso(),
            "reminder": reminder,
        }
        user["notes"].append(note)
        data["users"][user_id] = user
        self._write(data)
        return note_id

    def update_note(self, user_id: str, note_id: int, **fields: Any) -> bool:
        data = self._read()
        user = self._ensure_user(user_id)
        for n in user["notes"]:
            if n["id"] == note_id:
                n.update(fields)
                self._write(data)
                return True
        return False

    def delete_note(self, user_id: str, note_id: int) -> bool:
        data = self._read()
        user = self._ensure_user(user_id)
        before = len(user["notes"])
        user["notes"] = [n for n in user["notes"] if n["id"] != note_id]
        if len(user["notes"]) != before:
            self._write(data)
            return True
        return False

    def get_note(self, user_id: str, note_id: int) -> Optional[Dict[str, Any]]:
        user = self._ensure_user(user_id)
        for n in user["notes"]:
            if n["id"] == note_id:
                return n
        return None

    def list_notes_by_category(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        user = self._ensure_user(user_id)
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for c in user["categories"]:
            grouped[c["id"]] = []
        for n in user["notes"]:
            grouped.setdefault(n["category_id"], []).append(n)
        for v in grouped.values():
            v.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return grouped

    def search_notes(self, user_id: str, query: str) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        q = query.strip().lower()
        user = self._ensure_user(user_id)
        cat_by_id = {c["id"]: c for c in user["categories"]}
        results: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        for n in user["notes"]:
            cat = cat_by_id.get(n["category_id"], {"id": "general", "name": "عام"})
            haystack = f"{n['title']}\n{n['text']}\n{cat['name']}".lower()
            if q in haystack:
                results.append((n, cat))
        results.sort(key=lambda x: x[0].get("created_at", ""), reverse=True)
        return results

    def compute_stats(self, user_id: str) -> Dict[str, Any]:
        from datetime import datetime, timezone, timedelta
        user = self._ensure_user(user_id)
        notes = user["notes"]
        categories = user["categories"]
        now = datetime.now(timezone.utc)
        last7 = now - timedelta(days=7)
        recent = [n for n in notes if self._parse_iso(n["created_at"]) >= last7]
        per_cat = {}
        for c in categories:
            per_cat[c["name"]] = sum(1 for n in notes if n["category_id"] == c["id"])
        priorities = {"red": 0, "yellow": 0, "green": 0}
        for n in notes:
            priorities[n.get("priority", "green")] = priorities.get(n.get("priority", "green"), 0) + 1
        return {
            "total_notes": len(notes),
            "total_categories": len(categories),
            "recent_count": len(recent),
            "per_category": per_cat,
            "priorities": priorities,
        }

    def _parse_iso(self, s: str) -> datetime:
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return datetime.now(timezone.utc)