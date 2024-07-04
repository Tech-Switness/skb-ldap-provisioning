from werkzeug.serving import is_running_from_reloader

from src.app import create_app
from src.core.constants import settings
from src.services.scheduler import scheduler

app = create_app()

if __name__ == "__main__":
    try:
        if not is_running_from_reloader():
            scheduler.initialize()
        app.run(
            host='0.0.0.0',
            debug=settings.IS_RUNNING_LOCALLY
        )
    finally:
        scheduler.stop()
