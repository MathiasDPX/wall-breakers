from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Article(ABC):
    id: str
    headline: str
    subheadline: str
    content: list
    image: str

    @classmethod
    @abstractmethod
    def get_from_url(cls, url: str):
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__}(headline='{self.headline}')"