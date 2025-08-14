from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from typing import Callable, Optional

class ReminderScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.send_callback = None
    
    def set_send_callback(self, callback: Callable[[int, int], None]):
        self.send_callback = callback
    
    def add_reminder(self, user_id: int, note_id: int, reminder_time: str):
        try:
            dt = datetime.fromisoformat(reminder_time)
            if dt > datetime.now():
                self.scheduler.add_job(
                    func=self._send_reminder,
                    trigger=DateTrigger(run_date=dt),
                    args=[user_id, note_id],
                    id=f"reminder_{user_id}_{note_id}"
                )
        except Exception as e:
            print(f"Error scheduling reminder: {e}")
    
    def _send_reminder(self, user_id: int, note_id: int):
        if self.send_callback:
            self.send_callback(user_id, note_id)
    
    def remove_reminder(self, user_id: int, note_id: int):
        try:
            self.scheduler.remove_job(f"reminder_{user_id}_{note_id}")
        except:
            pass
    
    def shutdown(self):
        self.scheduler.shutdown()
