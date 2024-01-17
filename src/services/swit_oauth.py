import requests

from urllib.parse import urlencode

from src.core.constants import SWIT_BASE_URL, SWIT_CLIENT_SECRET, SWIT_CLIENT_ID
from src.database.crud import get_db_session, insert_swit_user_token, update_swit_user_token


def generate_login_url(redirect_uri: str, state: str) -> str:
    authorization_base_url = f'{SWIT_BASE_URL}/oauth/authorize'
    params = {
        'response_type': 'code',
        'client_id': SWIT_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'state': state,
        'scope': 'user:read admin:read admin:write'
    }
    return f'{authorization_base_url}?{urlencode(params)}'

def exchange_authorization_code_for_token(code: str, redirect_uri: str) -> None:
    """Exchange the authorization code for an access token."""
    token_url = f'{SWIT_BASE_URL}/oauth/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': SWIT_CLIENT_ID,
        'client_secret': SWIT_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=data)
    response.raise_for_status()  # Ensure to raise an exception for HTTP errors
    token_info = response.json()
    with get_db_session() as db_session:
        insert_swit_user_token(
            db_session,
            token_info['access_token'],
            token_info['refresh_token'],
        )

def refresh_access_token(refresh_token: str) -> None:
    """ Refresh swit token """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data_obj = {
        "grant_type": "refresh_token",
        "client_id": SWIT_CLIENT_ID,
        "client_secret": SWIT_CLIENT_SECRET,
        "refresh_token": refresh_token
    }

    token_url = f"{SWIT_BASE_URL}/oauth/token"
    res = requests.post(token_url, data=data_obj, headers=headers, timeout=10)
    res.raise_for_status()
    new_token_info = res.json()

    with get_db_session() as db_session:
        update_swit_user_token(
            db_session,
            access_token=new_token_info["access_token"],
            refresh_token=new_token_info["refresh_token"]
        )
