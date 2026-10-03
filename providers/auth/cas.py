import re
import threading
import time

import requests

from providers.exceptions import MediapartInvalidLogin

LOGIN_URL = "https://fscas01rp.c3rb.org/md34/login?service=https%3A%2F%2Fwww.mediapart.fr%2F%3Fcasid%3Dmd34"
SESSION_COOKIE = "mdpt_iam_sess"


class CASClient:
    _EXECUTION_VALUE_REGEX = re.compile(r'name="execution" value="([a-z0-9-]+_.+)"')

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.expire_at = 0

        self._lock = threading.Lock()
        self._refresh_thread = threading.Thread(
            target=self._auto_refresh_loop,
            daemon=True,
        )
        self._session = requests.Session()

    def start_refresh_loop(self):
        self._refresh_thread.start()

    def _auto_refresh_loop(self):
        # Refresh the token every 12 hours so they're always a fresh token and it doesn't take two bajillion years to get an article
        while True:
            self.refresh_token()
            time.sleep(12 * 60 * 60)

    def request(self, method: str, url: str, **kwargs):
        if time.time() > self.expire_at:
            self.refresh_token()

        response = self._session.request(
            method,
            url,
            **kwargs,
        )

        response.raise_for_status()
        return response

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def refresh_token(self):
        with self._lock:
            # Get execution parameter
            r = requests.get(LOGIN_URL)
            match = CASClient._EXECUTION_VALUE_REGEX.search(r.content.decode())

            if not match:
                raise MediapartInvalidLogin

            execution_value = match.group(1)

            body = {
                "username": self.username,
                "password": self.password,
                "_eventId": "submit",
                "submit": "SE CONNECTER",
                "execution": execution_value,
            }

            r = self._session.post(LOGIN_URL, data=body)
            for c in self._session.cookies:
                if c.name == SESSION_COOKIE:
                    self.expire_at = c.expires
                    return

            raise MediapartInvalidLogin