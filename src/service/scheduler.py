import threading
import time
import os

import schedule
import requests

def run_continuously(
    interval: int = 1
):
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread(name="idp_scheduler", daemon=True)
    continuous_thread.start()
    return cease_continuous_run

def background_job():
    header = {
        "x-secret-key": os.getenv("OPERATION_AUTH_KEY")
    }

    res1 = requests.post("http://localhost:5503/user_update",headers=header,timeout=10)
    print(res1.text)
