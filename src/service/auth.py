""" 인증 관련 모듈 """
import os
from typing import Final

import requests

# from ..database import crud

class GetTokenException(Exception):
    """ Get swit token exception """

def get_token(
    token_url: str,
    headers_obj: dict,
    data_obj: dict
) -> dict:
    """ get token info """
    res = requests.post(token_url, data=data_obj, headers=headers_obj, timeout=10)

    if res.ok:
        return res.json()

    raise GetTokenException(res.json())

def token_refresh(
    # db_session: crud.Session,
    # token: crud.model.SwitUserToken
):# -> crud.model.SwitUserToken:
    """ swit token 발급 및 앱 정보 저장 """
    header_obj: Final[dict] = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    data_obj: Final[dict] = {
        "grant_type": "refresh_token",
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "refresh_token": os.getenv("SWIT_REFRESH_TOKEN") # token.refresh_token
    }

    token_url = "https://openapi.swit.io/oauth/token"

    refresh_token = get_token(token_url, header_obj, data_obj)

    print("token refresh before")
    print(f"access token : {os.getenv('SWIT_ACCESS_TOKEN')}")
    print(f"refresh token : {os.getenv('SWIT_REFRESH_TOKEN')}")
    os.environ["SWIT_REFRESH_TOKEN"] = refresh_token["refresh_token"]
    os.environ["SWIT_ACCESS_TOKEN"] = refresh_token["access_token"]
    print("token refresh after")
    print(f"access token : {os.getenv('SWIT_ACCESS_TOKEN')}")
    print(f"refresh token : {os.getenv('SWIT_REFRESH_TOKEN')}")

    # crud.update_swit_user_token(
    #     db_session,
    #     access_token=refresh_token["access_token"],
    #     refresh_token=refresh_token["refresh_token"]
    # )

    # return crud.get_swit_user_token(db_session)
