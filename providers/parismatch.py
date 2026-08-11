import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure, fix_links, make_figcaption

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.parismatch\.com\/.+-(\d+)"
)


def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")

    fix_links(soup)

    return soup.decode_contents()


def _build_block(block):
    typename = block["type"]

    if typename == "text":
        return "<p>" + _sanitize_html(block["content"]) + "</p>"
    elif typename == "header":
        if block["level"] == 6:
            return ""

        return (
            f"<h{block['level']}>"
            + _sanitize_html(block["content"])
            + f"</h{block['level']}>"
        )

    return ""


class ParisMatchArticle(Article):
    SLUG = "pm"
    PROVIDER = "Paris Match"
    FAVICON = "https://www.parismatch.com/build/images/apple-touch-icon-114-precomposed.png"

    def __init__(self, article_id: str):
        data = ParisMatchArticle.get_data(article_id)

        image = data["image"]["url"]

        soup = BeautifulSoup(data["body"], features="html.parser")
        fix_links(soup)

        for element in soup.select("div.readtoo, div.embedded-entity"):
            element.decompose()

        content = (
            add_figure(image, make_figcaption(data['image']['description'], data['image']['credits']))
            + soup.decode_contents()
        )

        super().__init__(
            id=article_id,
            headline=data["title"],
            subheadline=data["intro"],
            content=content,
            url="https://www.parismatch.com"+data["uri"],
            image=image,
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)
    
    def get_data(id):
        r = requests.get(
            f"https://api-cms.parismatch.com/lmn_api/v1/node/article/{id}"
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = ParisMatchArticle.get_from_url(
        "https://www.parismatch.com/actu/politique/claude-chirac-on-a-tout-fait-des-cafes-aux-photocopies-273699"
    )

    print(article)
