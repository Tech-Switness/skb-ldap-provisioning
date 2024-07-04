from urllib.parse import urlencode

from httpx import Client

from src.core.constants import settings
from src.database import upsert_service_account
from src.services.swit_schemas import SwitTokens


def generate_login_url(redirect_uri: str) -> str:
    # TODO: Implement an encrypted state parameter to prevent CSRF attacks
    authorization_base_url = f'{settings.SWIT_BASE_URL}/oauth/authorize'
    params = {
        'response_type': 'code',
        'client_id': settings.SWIT_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': 'user:read admin:read admin:write'
    }
    return f'{authorization_base_url}?{urlencode(params)}'

def exchange_authorization_code_for_token(code: str, redirect_uri: str) -> None:
    """Exchange the authorization code for an access token."""
    token_url = f'{settings.SWIT_BASE_URL}/oauth/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': settings.SWIT_CLIENT_ID,
        'client_secret': settings.SWIT_CLIENT_SECRET,
    }
    with Client() as client:
        response = client.post(token_url, data=data)
    response.raise_for_status()  # Ensure to raise an exception for HTTP errors
    token_info = SwitTokens.model_validate(response.json())
    upsert_service_account(token_info)

def refresh_access_token(token_info: SwitTokens) -> None:
    """ Refresh swit token """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data_obj = {
        "grant_type": "refresh_token",
        "client_id": settings.SWIT_CLIENT_ID,
        "client_secret": settings.SWIT_CLIENT_SECRET,
        "refresh_token": token_info.refresh_token
    }

    token_url = f"{settings.SWIT_BASE_URL}/oauth/token"
    with Client() as client:
        res = client.post(token_url, data=data_obj, headers=headers, timeout=10)
        res.raise_for_status()
    new_token_json: dict[str, str] = res.json()
    token_info.access_token = new_token_json["access_token"]
    token_info.refresh_token = new_token_json["refresh_token"]
    upsert_service_account(token_info)
