import threading
import time
import schedule

from src.core.constants import SCHEDULE_TIME
from src.services.provision_manager import Provisioner


def _run_continuously(
        interval: int = 1
) -> threading.Event:
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls) -> None:
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread(name="idp_scheduler", daemon=True)
    continuous_thread.start()
    return cease_continuous_run


def _background_job() -> None:
    provisioner = Provisioner()
    provisioner.start_provisioning_thread()


def initialize_schedule() -> tuple[threading.Event | None, schedule.Job | None]:
    """Initialize scheduler"""
    schedule_event = job = None
    if SCHEDULE_TIME:
        schedule_event = _run_continuously()
        job = schedule.every().day.at(SCHEDULE_TIME).do(_background_job)
    return schedule_event, job


def stop_scheduler_if_exists(
        schedule_event: threading.Event | None,
        job: schedule.Job | None
) -> None:
    """Stop scheduler if exists"""
    if job:
        schedule.cancel_job(job)
    if schedule_event:
        schedule_event.set()
