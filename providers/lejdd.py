import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure, fix_links, make_figcaption

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.lejdd\.fr\/.+-(\d+)"
)


class JDDArticle(Article):
    SLUG = "jdd"
    PROVIDER = "Le Journal du Dimanche"
    
    def __init__(self, article_id: str):
        data = JDDArticle.get_data(article_id)
        
        soup = BeautifulSoup(data["body"], features="html.parser")
        
        
        for a in soup.find_all("a", href=True):
            # Decode article URLs
            if a["href"].startswith("/"):
                a["href"] = "https://www.lejdd.fr"+a["href"]
        
        fix_links(soup)
        
        for container in soup.select("div.readtoo"):
            container.decompose()
        
        content = soup.decode_contents()
        content = add_figure(data["image"]["url"], make_figcaption(data['image']['title'], data['image']['credits'])) + content

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
    
    def get_data(id):
        r = requests.get(f"https://api-cms.lejdd.fr/lmn_api/v1/node/article/{id}", headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0"
        })
        r.raise_for_status()
        
        return r.json()


if __name__ == "__main__":
    article = JDDArticle.get_from_url("https://www.lejdd.fr/culture/expositions-la-france-au-fil-de-lart-179928")

    print(article)
