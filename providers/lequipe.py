import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure, fix_link, fix_links

_URL_ID_PATTERN = re.compile(r"https:\/\/www\.lequipe\.fr\/.+\/(\d+)")


def _build_block(block):
    typename = block["__type"]

    if typename == "article_paragraph":
        if block["layout"] != "text":
            return ""

        return "<p>" + _sanitize_html(block.get("content", "")) + "</p>"
    elif typename == "article_paragraph_media":
        return add_figure(
            _build_media(block["media"], 1000), block["media"].get("legende")
        )

    return ""


def _get_item(items, layout):
    for item in items:
        if item["layout"] == layout:
            return item

    return None


def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")

    fix_links(soup)
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("/"):
            a["href"] = fix_link(f"https://www.lequipe.fr{a['href']}")

    return soup.decode_contents()


def _build_media(media, height):
    image = media["url"].replace("{width}", str(int(height * media["ratio"])))
    image = image.replace("{height}", str(height))
    image = image.replace("{quality}", "80")

    return image


class EquipeArticle(Article):
    SLUG = "ekip"
    PROVIDER = "L'Équipe"
    FAVICON = "https://www.lequipe.fr/favicons/favicon.svg"

    def __init__(self, article_id: str):
        data = EquipeArticle.get_data(article_id)

        content = ""
        body = _get_item(data["items"], "article_body")
        features = _get_item(data["items"], "article_feature")

        for block in body["objet"]["paragraphs"]:
            content += _build_block(block)

        if data["metas"]["sharing_image"]["ratio"] != -1:
            if data["metas"]["sharing_image"].get("formats") is None:
                image = data["metas"]["sharing_image"]["url"].replace("{width}", str(int(1000 * data["metas"]["sharing_image"]["ratio"])))
                image = image.replace("{height}", str(1000))
                image = image.replace("{quality}", "80")
            else:  
                image = _build_media(
                    data["metas"]["sharing_image"]["formats"]["landscape"], 1000
                )
            content = (
                add_figure(image, data["metas"]["sharing_image"].get("legende"))
                + content
            )
        else:
            image = None

        super().__init__(
            id=article_id,
            headline=features["objet"].get("long_title", features["objet"]["title"]),
            subheadline=data["metas"].get("description", ""),
            content=content,
            url=data["urls"]["web"],
            image=image,
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)
    
    def get_data(id):
        r = requests.get("https://dwh.lequipe.fr/api/v9/efr/news/" + id)

        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = EquipeArticle.get_from_url(
        "https://www.lequipe.fr/Football/Article/-il-montre-que-tout-le-monde-peut-reussir-dans-le-nord-de-marseille-la-castellane-est-fiere-de-zinedine-zidane-le-nouveau-selectionneur-des-bleus/1707695"
    )

    print(article)
