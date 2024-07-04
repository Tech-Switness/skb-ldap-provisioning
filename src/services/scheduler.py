import threading
import time
from typing import Optional

import schedule

from src.core.constants import settings
from src.services.provision_manager import provisioner


class _Scheduler:
    def __init__(self) -> None:
        self._event: Optional[threading.Event] = None
        self._job: Optional[schedule.Job] = None

    def initialize(self) -> None:
        """Initialize scheduler"""
        if not settings.SCHEDULE_TIME or self._job:
            return None
        self._run_continuously()
        self._job = schedule.every().day.at(settings.SCHEDULE_TIME).do(provisioner.start)
        print(f"Scheduled job: {self._job} at {settings.SCHEDULE_TIME}")

    def stop(self) -> None:
        """Stop scheduler if exists"""
        if self._job:
            schedule.cancel_job(self._job)
            print(f"Cancelled job: {self._job}")
        if self._event:
            self._event.set()
            print("Scheduler event set to cease continuous run.")

    def _run_continuously(self) -> None:
        self._event = event = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls) -> None:
                while not event.is_set():
                    schedule.run_pending()
                    time.sleep(60)

        continuous_thread = ScheduleThread(name="idp_scheduler", daemon=True)
        continuous_thread.start()


scheduler = _Scheduler()
