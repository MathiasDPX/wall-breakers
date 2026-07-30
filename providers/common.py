from abc import ABC, abstractmethod
from dataclasses import dataclass
import requests


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
    def __init__(self, refresh_token, client_id, token_url):
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.token_url = token_url
        self.access_token = None
        
    def _headers(self, **headers):
        return {
            "Authorization": f"Bearer {self.access_token}",
            **headers,
        }
        
    def refresh(self):
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


def add_figure(url, caption="", title=""):
    if not title:
        title = caption
    if not caption:
        caption = title

    caption = f"<figcaption>{caption}</figcaption>" if caption else ""
    title = f' title="{title}"' if title else ""

    return f'<figure><img src="{url}"{title}>{caption}</figure>'

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