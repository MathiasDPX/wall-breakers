import re

import requests
from bs4 import BeautifulSoup

from .common import Article

_URL_ID_PATTERN = re.compile(
    r".+lemonde\.fr\/.+_(\d+)_\d+\.html"
)


class LeMondeArticle(Article):
    SLUG = "lm"
    PROVIDER = "Le Monde"
    
    def __init__(self, article_id: str):
        r = requests.get(
            f"https://apps.lemonde.fr/aec/v1/premium-ios-tablet/article/{article_id}"
        )
        r.raise_for_status()
        data = r.json()

        soup = BeautifulSoup(data["template_vars"]["content"], features="html.parser")
        if soup.find_all("div", attrs={"class": "article_content"}):
            soup = soup.find_all("div", attrs={"class": "article_content"})[0]

        # Remove See Also, Inread, Video container and PubStack containers
        for container in soup.select("div.see-also-container, div.inread-container, div.video-container, div.pubstack-container, div.masthead, div.sections"):
            container.decompose()

        # Remove random link in figure
        for a in soup.find_all("a", role="button"):
            a.unwrap()

        # Obliterate script, style and aside
        for tag in soup.select("script, style, aside"):
            if tag.parent is not None:
                tag.decompose()

        for tag in soup.find_all():
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

        # Remove empty tags
        for tag in soup.find_all():
            if (
                not tag.get_text(strip=True)
                and not tag.find()
                and tag.name not in ["img", "br", "hr", "input"]
            ):
                tag.decompose()

        
        for a in soup.find_all("a", href=True):
            a["target"] = "_blank"
            
            # Decode article URLs
            if "lmfr://element/article" in a["href"]:
                a["href"] = a["href"].replace("lmfr://element/article/", "")
                a["href"] = a["href"].replace("?source=article_inline_link", "")

        image = "static/images/thumbnail.jpg"
        figure = soup.find('figure')
        if figure:
            img = figure.find('img')
            if img:
                image = img.get('src')
        
        content = soup.decode_contents()

        super().__init__(
            headline=data["template_vars"]["seo_title"],
            subheadline=data["template_vars"]["share_kicker"],
            content=content,
            url=data["element"]["url"],
            image=image
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)


if __name__ == "__main__":
    article = LeMondeArticle.get_from_url("https://www.lemonde.fr/planete/article/2026/07/18/au-canada-les-feux-a-repetition-bouleversent-la-foret-boreale_6724998_3244.html")

    print(article)
