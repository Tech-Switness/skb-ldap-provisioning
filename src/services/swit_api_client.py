""" Get Swit token """
import time
import requests

from typing import Any

from src.core.constants import SWIT_BASE_URL
from src.database.crud import get_db_session, get_swit_user_token
from src.core.logger import provisioning_logger as logger
from src.services.swit_oauth import refresh_access_token

_SWIT_REST_API_BASE_URL = SWIT_BASE_URL+'/v1/api'

class AuthenticatedRequests:
    """Makes request to the Swit API with the specified method, path and headers
        using the access token stored.
    """
    def __init__(self) -> None:
        with get_db_session() as db_session:
            token_info = get_swit_user_token(db_session)
            if not token_info:
                raise Exception("Swit token not found")
            self._token_info = token_info

    def requests(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        if not url.startswith('https://'):
            url = _SWIT_REST_API_BASE_URL + url

        res = requests.request(method, url, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token_info.access_token}"
        }, **kwargs)
        if res.status_code == 401 and not kwargs.get('refresh_tried'):  # token expired
            refresh_access_token(self._token_info)
            logger.info("Token refreshed")
            kwargs['refresh_tried'] = True
            res = self.requests(method, url, **kwargs)

        retry_after = kwargs.get('retry_after', 0)
        if res.status_code == 429 and retry_after < 5:  # Too many requests
            # Wait the specified number of seconds
            retry_after += 1
            logger.info(f"Too many requests. Waiting {retry_after} seconds for {url}...")
            time.sleep(retry_after)
            # Make the request again
            kwargs['retry_after'] = retry_after
            res = self.requests(method, url, **kwargs)

        return res
