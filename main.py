from src.app import create_app
from src.core.constants import IS_RUNNING_LOCALLY
from src.services.scheduler import initialize_schedule, stop_scheduler_if_exists


if __name__ == "__main__":
    app = create_app()
    schedule_event, job = initialize_schedule()
    try:
        app.run(
            host='0.0.0.0',
            debug=IS_RUNNING_LOCALLY
        )
    finally:
        stop_scheduler_if_exists(schedule_event, job)
