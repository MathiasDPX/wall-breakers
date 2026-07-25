from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Article(ABC):
    id: str
    headline: str
    subheadline: str
    content: list
    url: str
    image: str
    
    def __post_init__(self):
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


def add_figure(url, caption="", title=""):
    caption = f"<figcaption>{caption}</figcaption>" if caption else ""
    title = f" title=\"{title}\"" if title else ""
    
    return f'<figure{title}><img src="{url}">{caption}</figure>'
