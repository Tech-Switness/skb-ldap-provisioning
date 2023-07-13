""" api router """

import os
import secrets
import urllib
from functools import wraps

import requests
from flask import Flask, request, Response, redirect, url_for, session, abort
import threading

from .service import data_sync
from .database import crud

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Read secret key from an environment variable

def authenticate(func):
    '''This prevents other players from requesting for user update.'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("x-secret-key")
        if not auth_header:
            raise ValueError("x-secret-key header is missing")
        elif auth_header != os.getenv("OPERATION_AUTH_KEY"):
            raise ValueError('Invalid x-secret-key header')
        return func(*args, **kwargs)
    return wrapper

@app.errorhandler(ValueError)
def handle_auth_error(error):
    return {
        'message': str(error),
        'code': 'invalid_secret_key'
    }, 401


_PROVISIONING_THREAD: threading.Thread = None


def in_use():
    if not _PROVISIONING_THREAD or not _PROVISIONING_THREAD.is_alive():
        return False

    return True


@app.route("/user_update", methods=['POST'])
@authenticate
def provision_data():
    '''provision from AD to Swit'''
    if in_use():
        return Response("API is already in use.", status=409)
    else:
        global _PROVISIONING_THREAD
        _PROVISIONING_THREAD = threading.Thread(target=ldap_import.swit_user_update, daemon=True)
        _PROVISIONING_THREAD.start()
        return Response("Started provisioning.", status=200)


# OAuth2 client setup
client_id = os.getenv('CLIENT_ID')  # replace with your client ID (from Swit Developer Console)
client_secret = os.getenv('CLIENT_SECRET')  # replace with your client secret (from Swit Developer Console)
authorization_base_url = 'https://openapi.swit.io/oauth/authorize'
token_url = 'https://openapi.swit.io/oauth/token'

@app.route('/login')
def login():
    '''Login with Swit OAuth2'''
    # Generate a random state string and store it in the session
    state = secrets.token_hex(16)
    session['state'] = state  # In production, you may need to consider Radis or other cache systems

    # Generate the URL for the authorization request
    redirect_uri = request.url_root.strip('/').replace('http://','https://') + url_for('oauth_callback')  # Generate redirect URI dynamically

    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': state,
        'scope': 'user:read admin:read admin:write'
    }
    url = f'{authorization_base_url}?{urllib.parse.urlencode(params)}'

    # Redirect the user to the authorization URL
    return redirect(url)


@app.route('/oauth_callback')
def oauth_callback():
    '''OAuth2 callback'''
    # Get the authorization code and state from the request
    code = request.args.get('code')
    state = request.args.get('state')

    # Compare the state to the one stored in the session
    if state != session.get('state'):
        # If the states do not match, abort the request
        abort(403)

    # Make a POST request to the token URL to exchange the code for a token
    redirect_uri = request.base_url.replace('http://','https://')  # Use the current URL directly as redirect_uri
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    response = requests.post(token_url, data=data)
    token_info = response.json()

    with crud.get_db_session() as db_session:
        crud.insert_swit_user_token(
            db_session,
            token_info['access_token'],
            token_info['refresh_token'],
        )
    return '''<h1>You are logged in!</h1>'''
