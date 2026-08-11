import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure, fix_links

_URL_ID_PATTERN = re.compile(
    r"https:\/\/actu\.fr\/.+_(\d+)\.html"
)


class ActuArticle(Article):
    SLUG = "af"
    PROVIDER = "Actu.fr"
    FAVICON = "https://static.actu.fr/themes/actu_v2/dist/favicons/apple-touch-icon.png"
    
    def __init__(self, article_id: str):
        data = ActuArticle.get_data(article_id)
        
        soup = BeautifulSoup(data["content"], features="html.parser")
        
        for container in soup.select("div.ac-article-to-read, script"):
            container.decompose()
            
        for tag in soup.find_all():
            if (
                not tag.get_text(strip=True)
                and not tag.find()
                and tag.name not in ["img", "br", "hr", "input"]
            ):
                tag.decompose()
                
        for tag in soup.find_all():
            # Keep only allowed attributes
            tag.attrs = {
                key: value
                for key, value in tag.attrs.items()
                if key in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label",)
            }
            
        fix_links(soup)
        
        content = soup.decode_contents()
        
        content = add_figure(data["photo"]["file"], data["photo"]["caption"]) + content
        
        super().__init__(
            id=article_id,
            headline=data["title"],
            subheadline=data["chapo"],
            content=content,
            url=data["permalink"],
            image=data["photo"]["file"]
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)
    
    def get_data(id):
        r = requests.get(f"https://api.actu.fr/posts/{id}", headers={
            "HX-Request": "true",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        })
        r.raise_for_status()
        
        return r.json()["data"][0]


if __name__ == "__main__":
    article = ActuArticle.get_from_url("https://actu.fr/monde/deux-morts-et-18-000-cas-ce-que-l-on-sait-de-cette-epidemie-de-diarrhees-explosives-qui-sevit-aux-etats-unis_64626347.html")

    print(article)
