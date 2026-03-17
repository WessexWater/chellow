import os
from base64 import b64decode
from json import loads


class AuthNone:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ["REMOTE_USER"] = "admin"
        return self.app(environ, start_response)


class AuthMsEasyAuth:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        jwt_enc = environ["X-MS-CLIENT-PRINCIPAL"]
        jwt = loads(b64decode(jwt_enc))
        for claim in jwt["claims"]:
            if claim["typ"] == (
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
            ):
                username = claim["val"]
                environ["REMOTE_USER"] = username
        return self.app(environ, start_response)


class AuthMsIis:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        username = environ["HTTP_X_ISRW_PROXY_LOGON_USER"]
        environ["REMOTE_USER"] = username.upper()
        return self.app(environ, start_response)


USER_FUNCS = {
    None: AuthNone,
    "MS_IIS": AuthMsIis,
    "MS_EASY_AUTH": AuthMsEasyAuth,
}


def set_user_func(app):
    USER_AUTH = os.environ.get("USER_AUTH")
    return USER_FUNCS[USER_AUTH](app)
