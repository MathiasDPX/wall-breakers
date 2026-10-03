import re
import threading
import time

import requests


class SocialterClient:
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
        
    def create_account(self):
        with self._lock:
            