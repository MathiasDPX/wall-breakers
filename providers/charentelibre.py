import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure, fix_links, make_figcaption

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.charentelibre\.fr\/.+-(\d+)\.php"
)



class CharenteLibreArticle(Article):
    SLUG = "cl"
    PROVIDER = "Charente Libre"
    FAVICON = "https://www.charentelibre.fr/cl/android-icon-192x192.png"

    def __init__(self, article_id: str):
        data = CharenteLibreArticle.get_data(article_id)
        
        soup = BeautifulSoup(data["data"]["content"], features="html.parser")
        fix_links(soup)
        
        for container in soup.select("section.article-related"):
            container.decompose()
        
        for tag in soup.find_all():
            # Keep only allowed attributes
            tag.attrs = {
                key: value
                for key, value in tag.attrs.items()
                if key in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label",)
            }
            
        medias = data["data"]["media"]
        image_url = "static/images/thumbnail.jpg"
        content = soup.decode_contents()
        if len(medias) != 0:
            media = medias[0]
            image_url = media["uri"]
            
            legend = media.get("legend")
            author = media.get("author")
            
            content = add_figure(media["uri"], make_figcaption(legend, author)) + content
        
        super().__init__(
            id=data["id"],
            headline=data["title"],
            subheadline=data["head"],
            content=content,
            url="https://www.charentelibre.fr"+data["url"],
            image=image_url
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None
        
        return match.group(1)
        
    def get_data(id):
        r = requests.get(
            f"https://mag.gsoi.fr/articles/{id}?editor=cl"
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = CharenteLibreArticle.get_from_url(
        "https://www.charentelibre.fr/charente/champagne-mouton/cette-annee-on-va-s-interesser-au-theme-du-jardin-le-7e-festival-du-film-franco-britannique-de-champagne-mouton-cultive-son-originalite-30126109.php"
    )

    print(article)