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
    
    
def add_figure(url, caption):
    return f'<figure><img src="{url}"><figcaption>{caption}</figcaption></figure>'