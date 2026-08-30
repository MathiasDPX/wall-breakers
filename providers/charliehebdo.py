import re

import requests
from functools import lru_cache
from bs4 import BeautifulSoup

from .common import Article, fix_links, add_figure

_URL_PATTERN = re.compile(
    r"https:\/\/charliehebdo\.fr\/\d{4}\/\d{2}\/.+\/.+"
)

_ID_PATTERN = re.compile(
    r'class=".+ postid-(\d+) .+"'
)

class CharlieHebdoArticle(Article):
    SLUG = "ch"
    PROVIDER = "Charlie Hebdo"
    FAVICON = "https://charliehebdo.fr/wp-content/uploads/2019/05/sans-immage-150x150.png"

    def __init__(self, article_id: str):
        data = CharlieHebdoArticle.get_data(article_id)
        
        soup = BeautifulSoup(data["content"]["rendered"], features="html.parser")
        
        try:
            media_data_url = data["_links"]["wp:featuredmedia"][0]["href"]
            r = requests.get(media_data_url)
            r.raise_for_status()
            media_data = r.json()
            media = media_data["source_url"]
            figure = add_figure(media_data["link"], media_data["title"]["rendered"])
        except:
            media = "https://charliehebdo.fr/wp-content/uploads/2024/07/generique-article-web-foolz-e1724087479838.png"
            figure = ""
        
        for elem in soup.select("[data-a_lire_aussi_article]"):
            elem.decompose()

        for tag in soup.find_all():
            # Keep only allowed attributes
            tag.attrs = {
                key: value
                for key, value in tag.attrs.items()
                if key in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label",)
            }

        fix_links(soup)
        content = figure + soup.decode_contents()

        super().__init__(
            id=article_id,
            headline=data["title"]["rendered"],
            subheadline=data["acf"]["ch_post_chapo"],
            content=content,
            url=data["link"],
            image=media,
        )

    @lru_cache()
    def get_id_from_url(url: str):
        if _URL_PATTERN.search(url) is None:
            return None
        
        r = requests.get(url)
        r.raise_for_status()
        article_id = _ID_PATTERN.search(r.content.decode())
        if article_id is None:
            return None

        return article_id.group(1)
    
    def get_data(id):
        r = requests.get(f"https://charliehebdo.fr/wp-json/wp/v2/posts/{id}?appkey=JeSuisCharlie2023")
        r.raise_for_status()
        
        return r.json()


if __name__ == "__main__":
    article = CharlieHebdoArticle.get_from_url("https://charliehebdo.fr/2026/08/societe/faire-le-mont-blanc-pour-exister-comment-les-nouveaux-alpinistes-ruinent-la-montagne/")
    
    print(article)
