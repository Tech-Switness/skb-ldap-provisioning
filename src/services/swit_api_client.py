""" Get Swit token """
import time
import requests

from typing import Any

from src.core.constants import SWIT_BASE_URL
from src.database.crud import get_db_session, get_swit_user_token
from src.core.logger import provisioning_logger as logger
from src.services.swit_oauth import refresh_access_token

_SWIT_REST_API_BASE_URL = SWIT_BASE_URL+'/v1/api'

def authenticated_requests(method: str, url: str, **kwargs: Any) -> requests.Response:
    """Makes request to the Swit API with the specified method, path and headers"""
    with get_db_session() as db_session:
        token_info = get_swit_user_token(db_session)

    if not url.startswith('https://'):
        url = _SWIT_REST_API_BASE_URL + url

    res = requests.request(method, url, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token_info.access_token}"
    }, **kwargs)
    if res.status_code == 401 and not kwargs.get('refresh_tried'):  # token expired
        refresh_access_token(token_info.refresh_token)
        logger.info("Token refreshed")
        kwargs['refresh_tried'] = True
        res = authenticated_requests(method, url, **kwargs)

    retry_after = kwargs.get('retry_after', 0)
    if res.status_code == 429 and retry_after < 5:  # Too many requests
        # Wait the specified number of seconds
        retry_after += 1
        logger.info(f"Too many requests. Waiting {retry_after} seconds for {url}...")
        time.sleep(retry_after)
        # Make the request again
        kwargs['retry_after'] = retry_after
        res = authenticated_requests(method, url, **kwargs)

    return res
