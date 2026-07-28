import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.lejdd\.fr\/.+-(\d+)"
)


class JDDArticle(Article):
    SLUG = "jdd"
    PROVIDER = "Le Journal du Dimanche"
    
    def __init__(self, article_id: str):
        r = requests.get(f"https://api-cms.lejdd.fr/lmn_api/v1/node/article/{article_id}")
        r.raise_for_status()
        data = r.json()
        
        soup = BeautifulSoup(data["body"], features="html.parser")
        
        for a in soup.find_all("a", href=True):
            a["target"] = "_blank"
            href = a["href"]
            
            # Decode article URLs
            if "https://www.lejdd.fr/" in href:
                a["href"] = f"/{self.SLUG}/"+JDDArticle.get_id_from_url(href)
            elif href.startswith("/"):
                a["href"] = f"/{self.SLUG}/"+JDDArticle.get_id_from_url("https://www.lejdd.fr"+href)
        
        for container in soup.select("div.readtoo"):
            container.decompose()
        
        content = soup.decode_contents()
        content = add_figure(data["image"]["url"], f"{data['image']['title']} -- {data['image']['credits']}") + content

        super().__init__(
            id=article_id,
            headline=data["title"],
            subheadline=data["intro"],
            content=content,
            url="https://www.lejdd.fr"+data["uri"],
            image=data["image"]["url"]
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)


if __name__ == "__main__":
    article = JDDArticle.get_from_url("https://www.lejdd.fr/culture/expositions-la-france-au-fil-de-lart-179928")

    print(article)
