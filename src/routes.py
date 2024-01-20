""" api router """
import secrets

from functools import wraps
from typing import Callable, Any

import werkzeug
from flask import request, Response, redirect, url_for, session, abort, Blueprint, current_app

from src.services.provision_manager import Provisioner
from src.services.swit_oauth import generate_login_url, exchange_authorization_code_for_token

api = Blueprint('api', __name__)

def authenticate(func: Callable[..., Response]) -> Callable[..., Response]:
    """This prevents other players from requesting for user update."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Response:
        auth_header = request.headers.get("x-secret-key")
        if not auth_header:
            abort(401, "-secret-key header is missing")
        elif auth_header != current_app.config.get("SECRET_KEY"):
            abort(401, "Invalid x-secret-key header")
        return func(*args, **kwargs)
    return wrapper

@api.route("/user_update", methods=['POST'])
@authenticate
def provision_data() -> Response:
    provisioner = Provisioner()
    if not provisioner.start_provisioning_thread():
        abort(409, "API is already in use.")
    return Response("Started provisioning.", status=200)

@api.route('/login')
def login() -> werkzeug.wrappers.response.Response:
    """Login with Swit OAuth2"""
    state = secrets.token_hex(16)
    session['state'] = state
    redirect_uri = request.url_root.strip('/') + url_for(f'{api.name}.{oauth_callback.__name__}')
    if request.is_secure:
        redirect_uri = redirect_uri.replace('http://', 'https://')
    login_url = generate_login_url(redirect_uri, state)
    return redirect(login_url)

@api.route('/oauth_callback')
def oauth_callback() -> str:
    """OAuth2 callback"""
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        abort(400, 'code is missing')
    if state != session.get('state'):
        # If the states do not match, abort the request
        abort(403, 'Invalid state')

    redirect_uri = request.base_url
    if request.is_secure:
        redirect_uri = redirect_uri.replace('http://', 'https://')
    exchange_authorization_code_for_token(code, redirect_uri)
    return '<h1>You are logged in!</h1>'
