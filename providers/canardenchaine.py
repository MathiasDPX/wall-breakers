import re
import base64
from random import randint

import requests
from bs4 import BeautifulSoup
from flask import redirect

from .common import Article, fix_links

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.lecanardenchaine\.fr(\/.+\/\d+-.+)"
)

class CanardEnchaineArticle(Article):
    SLUG = "ce"
    PROVIDER = "Le Canard Enchainé"
    FAVICON = "https://www.lecanardenchaine.fr/static/favicon/icon.svg"

    def __init__(self, article_id: str):
        path = base64.b64decode(article_id).decode()
        data = CanardEnchaineArticle.get_data(article_id)
        
        soup = BeautifulSoup(data, features="html.parser")
        editorial = soup.select_one(".editorial")
        heading = soup.select_one("div.article__heading")
        
        og_url = soup.find("meta", property="og:image")
        og_url = og_url.get("content") if og_url else f"https://archives.lecanardenchaine.fr/static/img/og/le-canard-enchaine-0{randint(1,4)}.jpg"
        
        subheadline_element = editorial.select_one("h2.editorial__chapo")
        if subheadline_element is not None:
            subheadline = subheadline_element.decode_contents()
        else:
            subheadline = ""
            
        subheadline_element.decompose()
        headline = heading.select_one("span.title-optimized__title").decode_contents()
        
        for elem in editorial.select("figure a"):
            elem.unwrap()
            
        for elem in editorial.select("figcaption *"):
            elem.unwrap()
        
        for tag in soup.find_all():
            # Keep only allowed attributes
            tag.attrs = {
                key: value
                for key, value in tag.attrs.items()
                if key in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label",)
            }
            
        fix_links(editorial)

        super().__init__(
            id=article_id,
            headline=headline,
            subheadline=subheadline,
            content=editorial.decode_contents(),
            url="https://www.lecanardenchaine.fr"+path,
            image=og_url,
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return base64.b64encode(match.group(1).encode()).decode("ascii")
    
    def get_data(id):
        article_path = base64.b64decode(id).decode()
        r = requests.get("https://www.lecanardenchaine.fr"+article_path, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "X-Forwarded-For": "66.249.66.1"
        })
        
        r.raise_for_status()
        
        return r.content
    
    def get_readable_data(id):
        return redirect("./raw")


if __name__ == "__main__":
    article = CanardEnchaineArticle.get_from_url("https://www.lecanardenchaine.fr/international/54740-la-castagne-au-canada")
    
    print(article)
