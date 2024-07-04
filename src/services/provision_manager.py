import threading
from typing import Optional

from src.services.data_sync import sync_to_swit


class _Provisioner:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        print("Provisioner start")
        if self.is_in_progress:
            return None
        self._thread = threading.Thread(target=sync_to_swit)
        self._thread.start()

    @property
    def is_in_progress(self) -> bool:
        return bool(self._thread and self._thread.is_alive())


provisioner = _Provisioner()
