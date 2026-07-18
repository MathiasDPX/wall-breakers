from dataclasses import dataclass
import requests
import re


_URL_ID_PATTERN = re.compile(r'.+-\d{2}-\d{2}-\d{4}-([A-Z0-9]{26})\.php')

@dataclass
class Article:
    def __init__(self, id):
        r = requests.get(f"https://gateway-api.leparisien.fr/v1/contents/articles/{id}")
        r.raise_for_status()
        data = r.json()["story"]
        
        self.id = data["_id"]
        self.headline = data["headlines"]["basic"]
        self.subheadline = data["subheadlines"]["basic"]
        self.content = data["bodyContent"]
        
        self.image = data["promo_items"]["basic"]["resize_url"]
        self.image_copyright = data["promo_items"]["basic"]["copyright"]
        self.image_caption = data["promo_items"]["basic"]["url"]
        
    @classmethod
    def get_from_url(cls, url: str) -> "Article":
        matches = _URL_ID_PATTERN.findall(url)
        if len(matches) != 1:
            print(url)
            return None
        
        return cls(matches[0])
    
    def __repr__(self):
        return f"Article(headline='{self.headline}')"
    
    
    
if __name__ == "__main__":
    article = Article.get_from_url("https://www.leparisien.fr/sports/football/coupe-du-monde/france-angleterre-la-composition-probable-des-bleus-avec-zaire-emery-cherki-olise-et-mbappe-18-07-2026-ZMLNSNIHBVGEPALOLJ3KGMBQAI.php")

    print(article)