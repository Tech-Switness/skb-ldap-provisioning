"""
Makes request to the Swit API using the access token stored.
"""
import time
from httpx import Client, Response

from typing import Any

from src.core.constants import settings
from src.core.logger import provisioning_logger as logger
from src.database import get_service_account
from src.services.swit_oauth import refresh_access_token


class SwitApiClient(Client):
    def __init__(self) -> None:
        super().__init__(
            timeout=10,
            base_url=settings.SWIT_BASE_URL + '/v1/api'
        )
        self._token_info = get_service_account()
        self._update_token_header()

    def request(self, *args: Any, **kwargs: Any) -> Response:
        res = super().request(*args, **kwargs)
        if res.status_code == 401:
            refresh_access_token(self._token_info)
            self._update_token_header()
            logger.info("Token refreshed")
            res = super().request(*args, **kwargs)

        retry_after = int(res.request.headers.get('x-retry-after', '0'))
        if res.status_code == 429 and retry_after < 5:  # Too many requests
            # Wait the specified number of seconds
            retry_after += 1
            logger.info(f"Too many requests. Waiting {retry_after} seconds for {res.request.url}...")
            time.sleep(retry_after)
            # Make the request again
            res.request.headers.update({'x-retry-after': str(retry_after)})
            kwargs['headers'] = res.request.headers
            res = self.request(*args, **kwargs)

        if not res.is_success:
            logger.error(f"Failed request: {res.request.content.decode('utf-8')}")
        res.raise_for_status()
        return res

    def _update_token_header(self) -> None:
        self.headers.update({
            "Authorization": f"Bearer {self._token_info.access_token}"
        })
