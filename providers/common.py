from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Article(ABC):
    # Providers sharing a GROUP are displayed as a single entry
    GROUP = None
    # Set to False to keep a provider out of the advertised source list
    LISTED = True

    id: str
    headline: str
    subheadline: str
    content: list
    url: str
    image: str
    publication_date: datetime | None = None


    def __post_init__(self):
        self.raw_id = self.id
        self.id = f"{self.PROVIDER}:{self.id}"

    @property
    def local_publication_date(self) -> datetime | None:
        """Publication date, timezone-aware dates converted to the server timezone."""
        if self.publication_date is None:
            return None

        if self.publication_date.tzinfo is None:
            return self.publication_date

        return self.publication_date.astimezone()

    @property
    def has_publication_time(self) -> bool:
        """False when the publication date only carries a day, i.e. it lands on midnight."""
        publication_date = self.local_publication_date

        if publication_date is None:
            return False

        return (publication_date.hour, publication_date.minute, publication_date.second, publication_date.microsecond) != (0, 0, 0, 0)

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

    @classmethod
    def is_enabled(cls) -> bool:
        """Whether the provider can be used with the current configuration."""
        return True


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
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
        }


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
