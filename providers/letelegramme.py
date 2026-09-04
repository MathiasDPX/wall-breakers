import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure, fix_links, make_figcaption

_URL_ID_PATTERN = re.compile(r".+letelegramme\.fr\/.+-(\d+)\.php")

_HEADERS = {"x-tlg-api-key": "Tftd9qndckFJWEvuj5tprjcLtWeQpr1F"}


class LeTelegrammeArticle(Article):
    SLUG = "lt"
    PROVIDER = "Le Télégramme"
    FAVICON = "https://www.letelegramme.fr/apple-touch-icon.png?39cabe1fd9d9dbd0ebb82fc497f4728bad450ad4-1786351968"
    
    def __init__(self, article_id: str):
        data = LeTelegrammeArticle.get_data(article_id)

        soup = BeautifulSoup("".join(data["content"]), features="html.parser")
        if soup.find_all("div", attrs={"class": "article_content"}):
            soup = soup.find_all("div", attrs={"class": "article_content"})[0]

        # Remove random link in figure
        for a in soup.find_all("a", role="button"):
            a.unwrap()

        # Remove See Also, Inread, Video container and PubStack containers
        for container in soup.select("span.a-lire-aussi, span.lien-rebond-title"):
            container.decompose()

        # Obliterate script, style and aside
        for tag in soup.select("script, style, aside"):
            if tag.parent is not None:
                tag.decompose()

        # Reformat headings from "1 Heading text" to "1. Heading text"
        for h2 in soup.find_all("h2", class_="numero"):
            h2.string = re.sub(r"^(\d+)\s+", r"\1. ", h2.get_text())

        for tag in soup.find_all():
            # Keep only allowed tags
            if tag.name not in ("figure", "figcaption", "p", "em", "a", "img", "h1", "h2", "h3", "h4", "h5", "h6", "b", "ul", "li"):
                tag.unwrap()
                continue

            # Keep only allowed attributes
            tag.attrs = {
                key: value
                for key, value in tag.attrs.items()
                if key
                in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label")
            }

        # Remove empty tags
        for tag in soup.find_all():
            if (
                not tag.get_text(strip=True)
                and not tag.find()
                and tag.name not in ["img", "br", "hr", "input"]
            ):
                tag.decompose()

        fix_links(soup)

        content = soup.decode_contents()

        image = "static/images/thumbnail.jpg"
        for addon in data["addons"]:
            if addon["type"] != "MED:IMG:":
                continue
                
            image = f"https://media.letelegramme.fr/api/v1/images/view/{addon['idImg']}/web_golden_xxl/{addon['idImg']}.1"
            content = add_figure(image, make_figcaption(addon.get('title'), addon.get('credits'))) + content

        super().__init__(
            id=article_id,
            headline=data["title"],
            subheadline=data["lead"],
            content=content,
            url="https://www.letelegramme.fr" + data["url"],
            image=image,
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)
    
    def get_data(id):
        r = requests.get(
            f"https://api.letelegramme.fr/editorial/www0f/elements/{id}?mode=full",
            headers=_HEADERS,
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = LeTelegrammeArticle.get_from_url(
        "https://www.letelegramme.fr/finistere/landerneau-29800/a-landerneau-une-journee-pour-celebrer-la-culture-bretonne-le-25-juillet-avec-fest-e-landerne-7086034.php"
    )

    print(article)
