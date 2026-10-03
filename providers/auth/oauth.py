import json
import os
import threading
import time
from hashlib import sha256
from pathlib import Path

import requests


class OAuthClient:
    def __init__(self, refresh_token, client_id, token_url, data_dir=None):
        self.access_token = None
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.token_url = token_url
        self._token_path = Path(
            data_dir or os.getenv("DATA_DIR", "data")
        ) / f"oauth-{self.client_id}.json"

        self._lock = threading.Lock()
        self._refresh_token_hash = sha256(refresh_token.encode("utf-8")).hexdigest()
        self._refresh_thread = threading.Thread(
            target=self._auto_refresh_loop,
            daemon=True,
        )

        if self._token_path.is_file():
            with self._token_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            original_refresh_token_hash = data.get("original_refresh_token_hash", "")
            self.access_token = data.get("access_token", None)
            self.refresh_token = data.get("refresh_token", self.refresh_token)

            if original_refresh_token_hash != self._refresh_token_hash:
                self.refresh_token = refresh_token
                self.refresh()

    def _auto_refresh_loop(self):
        # Preventive refresh every 24 hours in case nobody sent a request to Ouest-France
        while True:
            self.refresh()
            time.sleep(24 * 60 * 60)  # Wait 24 hours

    def start_refresh_loop(self):
        self._refresh_thread.start()

    def _headers(self, **headers):
        return {
            "Authorization": f"Bearer {self.access_token}",
            **headers,
        }

    def refresh(self):
        with self._lock:
            r = requests.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                },
            )
            r.raise_for_status()

            token = r.json()
            self.access_token = token["access_token"]

            if "refresh_token" in token:
                self.refresh_token = token["refresh_token"]

            self._token_path.parent.mkdir(parents=True, exist_ok=True)
            with self._token_path.open("w", encoding="utf-8") as f:
                json.dump({
                    "refresh_token": self.refresh_token,
                    "access_token": self.access_token,
                    "original_refresh_token_hash": self._refresh_token_hash

                }, f, ensure_ascii=False)

            return token

    def request(self, method: str, url: str, retry=True, **kwargs):
        headers = kwargs.pop("headers", {})
        response = requests.request(
            method,
            url,
            headers=self._headers(**headers),
            **kwargs,
        )

        if response.status_code == 401 and retry:
            self.refresh()
            return self.request(method, url, retry=False, headers=headers, **kwargs)

        response.raise_for_status()
        return response

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)