""" api router """

import os
from functools import wraps

from flask import Flask,request,Response
import threading

from .service import ldap_import#, auth
# from .database import crud

app = Flask(__name__)
_IN_USAGE_PROVISIONING = False

def authenticate(func):
    '''authenticate with secret key'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("x-secret-key")
        if not auth_header:
            raise ValueError("x-secret-key header is missing")
        elif auth_header != os.getenv("X_SECRET_KEY"):
            raise ValueError('Invalid x-secret-key header')
        return func(*args, **kwargs)
    return wrapper

@app.errorhandler(ValueError)
def handle_auth_error(error):
    return {
        'message': str(error),
        'code': 'invalid_secret_key'
    }, 401
_PROVISIONING_THREAD:threading.Thread = None

def in_usage():
    if not _PROVISIONING_THREAD or not _PROVISIONING_THREAD.is_alive():
        return False

    return True

@app.route("/user_update", methods=['POST'])
@authenticate
def provision_data():
    '''provision from AD to Swit'''
    if in_usage():
        return Response("API is already in use.", status=200)
    else:
        global _PROVISIONING_THREAD
        _PROVISIONING_THREAD = threading.Thread(target=ldap_import.swit_user_update,daemon=True)
        _PROVISIONING_THREAD.start()
        return Response("Started provisioning.", status=200)
