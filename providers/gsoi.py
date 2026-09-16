import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure, fix_links, make_figcaption


class GSOIArticle(Article):
    EDITION = None

    def __init__(self, article_id: str):
        data = self.get_data(article_id)
        
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
            url=f"https://www.{self.DOMAIN}.fr{data['url']}",
            image=image_url
        )
    
    @classmethod
    def get_id_from_url(cls, url: str):
        match = re.compile(r"https:\/\/www\."+cls.DOMAIN+r"\.fr\/.+-(\d+)\.php").search(url)
        if match is None:
            return None
        
        return match.group(1)

    @classmethod
    def get_data(cls, id):
        r = requests.get(
            f"https://mag.gsoi.fr/articles/{id}?editor={cls.EDITION}"
        )

        r.raise_for_status()
        return r.json()


class SudOuestArticle(GSOIArticle):
    SLUG = "so"
    PROVIDER = "Sud Ouest"
    FAVICON = "https://www.sudouest.fr/so/android-icon-192x192.png"

    DOMAIN = "sudouest"
    EDITION = "so"

class CharenteLibreArticle(GSOIArticle):
    SLUG = "cl"
    PROVIDER = "Charente Libre"
    FAVICON = "https://www.charentelibre.fr/cl/android-icon-192x192.png"

    DOMAIN = "charentelibre"
    EDITION = "cl"

class RepubliquePyreneesArticle(GSOIArticle):
    SLUG = "rep"
    PROVIDER = "La République des Pyrénées"
    FAVICON = "https://www.larepubliquedespyrenees.fr/rep/android-icon-192x192.png"

    DOMAIN = "larepubliquedespyrenees"
    EDITION = "rep"


if __name__ == "__main__":
    article = RepubliquePyreneesArticle.get_from_url(
        "https://www.larepubliquedespyrenees.fr/economie/transports/train/pyrenees-atlantiques-panne-d-electricite-geante-a-la-sncf-la-galere-des-usagers-video-30653617.php"
    )

    print(article)

    article = SudOuestArticle.get_from_url(
        "https://www.sudouest.fr/gironde/bordeaux/info-sud-ouest-romain-dupuy-de-retour-a-cadillac-dans-une-unite-fermee-apres-trois-ans-a-l-hopital-psychiatrique-de-bordeaux-30653312.php"
    )

    print(article)

    article = CharenteLibreArticle.get_from_url(
        "https://www.charentelibre.fr/charente/champagne-mouton/cette-annee-on-va-s-interesser-au-theme-du-jardin-le-7e-festival-du-film-franco-britannique-de-champagne-mouton-cultive-son-originalite-30126109.php"
    )

    print(article)