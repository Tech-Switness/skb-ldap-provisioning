""" main """
import os

import dotenv
dotenv.load_dotenv()

from src.service import scheduler
from src import api

print("시작")
if __name__ == "__main__":
    schedule_event = scheduler.run_continuously()
    job = scheduler.schedule.every().day.at("20:00").do(scheduler.background_job)
    try:
        if os.getenv('IS_RUNNING_LOCALLY'):
            print('locally_running')
            api.app.run(host='0.0.0.0',debug=True, port=os.getenv("LDAP_PORT"))
        else:
            print('running on the server')
            api.app.run(host='0.0.0.0',debug=False,port=os.getenv("LDAP_PORT"))
    finally:
        scheduler.schedule.cancel_job(job)
        schedule_event.set()
