import threading
from typing import Optional

from src.services.data_sync import SyncToSwit


class Provisioner:
    _instance: Optional['Provisioner'] = None

    def __new__(cls) -> 'Provisioner':
        if cls._instance is None:
            cls._instance = super(Provisioner, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Ensure that initialization happens only once
        if not hasattr(self, '_provisioning_thread'):
            self._provisioning_thread: Optional[threading.Thread] = None

    def start_provisioning_thread(self) -> bool:
        if self._is_provisioning():
            return False
        # Replace `sync_to_swit` with the actual target function for the thread
        sync_to_swit = SyncToSwit()
        self._provisioning_thread = sync_to_swit.thread
        self._provisioning_thread.start()
        return True

    def _is_provisioning(self) -> bool:
        return self._provisioning_thread is not None and self._provisioning_thread.is_alive()

