import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure, fix_links, make_figcaption

_URL_ID_PATTERN = re.compile(
    r".+lesechos.fr\/.+-(\d+)"
)


class LesEchosArticle(Article):
    SLUG = "le"
    PROVIDER = "Les Echos"
    FAVICON = "https://www.lesechos.fr/assets/les-echos/020128d1da0fecffdf3de5ff92440a19.webp"
    
    def __init__(self, article_id: str):
        data = LesEchosArticle.get_data(article_id)

        soup = BeautifulSoup(data["description"], features="html.parser")

        # Remove See Also
        for container in soup.select("div.encadre-lire-aussi"):
            container.decompose()
        
        fix_links(soup)

        image = f"https://media.lesechos.com/api/v1/images/view/{data['image']['id']}/976x549-webp/{data['image']['filename']}"
        
        content = soup.decode_contents()
        content = add_figure(image, make_figcaption(data['image']['caption'], data['image']['credits'])) + content

        super().__init__(
            id=article_id,
            headline=data["title"],
            subheadline=data["lead"],
            content=content,
            url="https://www.lesechos.fr"+data["path"],
            image=image
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)
    
    def get_data(id):
        r = requests.get(
            f"https://api.lesechos.fr/api/v2/posts/{id}",
            headers={
                "Host": "api.lesechos.fr",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
            }
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = LesEchosArticle.get_from_url("https://www.lesechos.fr/monde/etats-unis/lespagne-gagne-la-coupe-du-monde-de-foot-et-la-fifa-empoche-un-pactole-2243070")

    print(article)
