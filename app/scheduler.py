from datetime import datetime, timedelta, timezone
from typing import Callable, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import logging

logger = logging.getLogger(__name__)


class ReminderScheduler:
    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(timezone=timezone.utc)
        self.scheduler.start()
        self._send_callback: Optional[Callable[[int, int], None]] = None

    def set_send_callback(self, callback: Callable[[int, int], None]) -> None:
        self._send_callback = callback

    def schedule(self, user_id: int, note_id: int, run_at_iso: str) -> str:
        run_at = datetime.fromisoformat(run_at_iso)
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=timezone.utc)
        trigger = DateTrigger(run_date=run_at)
        job = self.scheduler.add_job(self._on_fire, trigger=trigger, args=[user_id, note_id])
        logger.info("Scheduled reminder note=%s user=%s at=%s", note_id, user_id, run_at_iso)
        return job.id

    def cancel(self, job_id: str) -> None:
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass

    def _on_fire(self, user_id: int, note_id: int) -> None:
        if self._send_callback is None:
            logger.warning("No send callback set; cannot send reminder")
            return
        try:
            self._send_callback(user_id, note_id)
        except Exception as e:
            logger.exception("Failed to send reminder: %s", e)

    def shutdown(self) -> None:
        try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            pass