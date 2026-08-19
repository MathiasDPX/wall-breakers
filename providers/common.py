import json
import os
import re
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import requests

from .exceptions import MediapartInvalidLogin


@dataclass
class Article(ABC):
    id: str
    headline: str
    subheadline: str
    content: list
    url: str
    image: str

    def __post_init__(self):
        self.raw_id = self.id
        self.id = f"{self.PROVIDER}:{self.id}"

    @classmethod
    def get_from_url(cls, url: str):
        id = cls.get_id_from_url(url)
        if id is None:
            return None

        return cls(id)

    @abstractmethod
    def get_id_from_url(url: str):
        raise NotImplementedError

    @abstractmethod
    def get_data(id: str):
        raise NotImplementedError
    
    def get_readable_data(id: str):
        raise NotImplementedError


    def __repr__(self):
        return f"{self.__class__.__name__}(headline='{self.headline}')"

    def asdict(self):
        return {
            "success": True,
            "id": self.id,
            "headline": self.headline,
            "subheadline": self.subheadline,
            "content": self.content,
            "url": self.url,
            "image": self.image,
        }


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
            r = requests.get("https://fscas01rp.c3rb.org/md34/login?service=https%3A%2F%2Fwww.mediapart.fr%2F%3Fcasid%3Dmd34")
            match = CASClient._EXECUTION_VALUE_REGEX.search(r.content.decode())
            
            if not match:
                raise MediapartInvalidLogin
        
            execution_value = match.group(1)
            
            body = {
                "username": self.username,
                "password": self.password,
                "_eventId": "submit",
                "submit": "SE CONNECTER",
                "execution": execution_value
            }

            r = self._session.post("https://fscas01rp.c3rb.org/md34/login?service=https%3A%2F%2Fwww.mediapart.fr%2F%3Fcasid%3Dmd34", data=body)
            for c in self._session.cookies:
                if c.name == "mdpt_iam_sess":
                    self.expire_at = c.expires
                    return
            
            raise MediapartInvalidLogin
        

def add_figure(url:str, caption="", title=""):
    if not title:
        title = caption
    if not caption:
        caption = title

    caption = f"<figcaption>{caption}</figcaption>" if caption else ""
    title = f' title="{title}"' if title else ""
    
    if not url.endswith(".mp4"):
        media = f'<img src="{url}"{title}>'
    else:
        media = f'<video controls src="{url}"{title}>'
        

    return f'<figure>{media}{caption}</figure>'

def get_article_from_url(url: str):
    from .registry import PROVIDERS

    for provider in PROVIDERS:
        id = provider.get_id_from_url(url)
        if id is not None:
            return provider, id

    return None, None


def fix_links(soup):
    for a in soup.find_all("a", href=True):
        a["target"] = "_blank"
        a["href"] = fix_link(a["href"])
        
def fix_link(url):        
    provider, id = get_article_from_url(url)
    
    if id is None:
        return url
    
    return f"/{provider.SLUG}/{id}"

def make_figcaption(caption, credit):
    if credit is not None and credit.strip().startswith("©"):
        credit = credit.replace("©", "")
        
    if caption is None and credit is None:
        return ""
    elif caption is None:
        return "&copy; " + credit
    elif credit is None:
        return caption
    else:
        return caption + " &copy; " + credit
