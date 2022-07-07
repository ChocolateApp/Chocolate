import os

from tmdbv3api.exceptions import TMDbException
from tmdbv3api.tmdb import TMDb


class Authentication(TMDb):
    _urls = {
        "create_request_token": "/authentication/token/new",
        "validate_with_login": "/authentication/token/validate_with_login",
        "create_session": "/authentication/session/new",
    }

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
        self.expires_at = None
        self.request_token = self._create_request_token()
        self._authorise_request_token_with_login()
        self._create_session()

    def _create_request_token(self):
        """
        Create a temporary request token that can be used to validate a TMDb user login.
        """
        resp = self._call(self._urls["create_request_token"], "")
        self.expires_at = resp["expires_at"]
        return resp["request_token"]

    def _create_session(self):
        """
        You can use this method to create a fully valid session ID once a user has validated the request token.
        """
        data = {"request_token": self.request_token}

        req = self._call(
            action=self._urls["create_session"],
            append_to_response="",
            method="POST",
            data=data,
        )

        os.environ["TMDB_SESSION_ID"] = req["session_id"]

    def _authorise_request_token_with_login(self):
        """
        This method allows an application to validate a request token by entering a username and password.
        """
        data = {
            "username": self.username,
            "password": self.password,
            "request_token": self.request_token,
        }

        resp = self._call(
            action=self._urls["validate_with_login"],
            append_to_response="",
            method="POST",
            data=data,
        )

        if "success" not in resp:
            raise TMDbException(resp["status_message"])
