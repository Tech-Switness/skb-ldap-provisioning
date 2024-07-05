from werkzeug.serving import is_running_from_reloader

from src.app import create_app
from src.core.constants import settings
from src.services.provision_manager import provisioner
from src.services.scheduler import scheduler

app = create_app()

if __name__ == "__main__":
    try:
        if not is_running_from_reloader():
            scheduler.initialize()
            # At start, provisioner will be started
            provisioner.start()
        app.run(
            host='0.0.0.0',
            port=settings.PORT,
            debug=settings.IS_RUNNING_LOCALLY
        )
    finally:
        scheduler.stop()
