class ReminderScheduler:
    def __init__(self):
        self.send_callback = None
    
    def set_send_callback(self, callback):
        self.send_callback = callback
    
    def add_reminder(self, user_id: int, note_id: int, reminder_time: str):
        # سيتم تطويرها لاحقاً
        pass
    
    def remove_reminder(self, user_id: int, note_id: int):
        # سيتم تطويرها لاحقاً
        pass
    
    def shutdown(self):
        # سيتم تطويرها لاحقاً
        pass
