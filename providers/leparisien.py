from .common import Article
from bs4 import BeautifulSoup
import re
import requests


_URL_ID_PATTERN = re.compile(
    r".+-\d{2}-\d{2}-\d{4}-([A-Z0-9]{26})\.php"
)



class LeParisienArticle(Article):

    def __init__(self, article_id: str):
        r = requests.get(
            f"https://gateway-api.leparisien.fr/v1/contents/articles/{article_id}"
        )
        r.raise_for_status()
        data = r.json()["story"]
        
        content = data["bodyContent"]
        
        soup = BeautifulSoup(content, features="html.parser")
        
        # Remove See Also
        for container in soup.select("div.article-read-also_container"):
            container.decompose()
        
        for tag in soup.find_all():
            # Obliterate unwanted tags
            if tag.name in ("script", "style", "link"):
                tag.decompose()
                continue
            
            # Keep only allowed tags
            if tag.name not in ("figure", "figcaption", "p", "em", "a", "img", "h1", "h2", "h3", "h4", "h5", "h6", "b", "ul", "li"):
                tag.unwrap()
                continue
            
            # Keep only allowed attributes
            tag.attrs = {
                key: value
                for key, value in tag.attrs.items()
                if key in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label",)
            }
            
            for a in soup.find_all("a", href=True):
                a["target"] = "_blank"
            
                # Decode article URLs
                if "https://www.leparisien.fr/" in a["href"]:
                    id = LeParisienArticle.get_id_from_url(a["href"])
                    if id != None:
                        a["href"] = f"/lp/{id}"
            
        content = soup.decode_contents()


        super().__init__(
            id="leparisien:"+data["_id"],
            headline=data["headlines"]["basic"],
            subheadline=data["subheadlines"]["basic"],
            content=content,
            url="https://www.leparisien.fr"+data["canonical_url"]
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None
        
        return match.group(1)
        


if __name__ == "__main__":
    article = LeParisienArticle.get_from_url(
        "https://www.leparisien.fr/sports/football/coupe-du-monde/france-angleterre-la-composition-probable-des-bleus-avec-zaire-emery-cherki-olise-et-mbappe-18-07-2026-ZMLNSNIHBVGEPALOLJ3KGMBQAI.php"
    )

    print(article)