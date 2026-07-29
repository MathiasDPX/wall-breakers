import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.liberation\.fr\/.+-\d{8}_([A-Z0-9]+)(?:.+)?"
)

_HEADERS = {"x-api-key": "a7X29mBvQeP1Ld98CgF2rK5uTzWY4h"}  # Mobile app apikey


def get_audio_url(article_url):
    data = {
        "forceRegeneration": False,
        "loadProduction": False,
        "parseOnly": False,
        "templateName": "liberation_random_voice",
        "url": article_url,
    }

    r = requests.post(
        "https://api.podle.io/v1/player/read",
        json=data,
        headers={
            "Authorization": "Bearer f253235592a3c380ef007b488dc879852d7418c2170cf1dc67343babf5ddcd6d"
        },
    )
    r.raise_for_status()

    return r.json()


def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")

    for a in soup.find_all("a", href=True):
        a["target"] = "_blank"

        id = LiberationArticle.get_id_from_url(a["href"])
        if id is not None:
            a["href"] = f"/{LiberationArticle.SLUG}/{id}"

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


class LiberationArticle(Article):
    SLUG = "lib"
    PROVIDER = "Libération"

    def __init__(self, article_id: str):
        params = {
            "website": "liberation",
            "_id": article_id,
        }
        r = requests.get(
            "https://arc.api.liberation.fr/content/v4/", headers=_HEADERS, params=params
        )
        r.raise_for_status()
        data = r.json()

        content = ""
        for block in data["content_elements"]:
            content += _build_block(block)

        image = data["promo_items"]["basic"]["additional_properties"]["originalUrl"]
        url = "https://www.liberation.fr" + data["canonical_url"]

        copyright = data["promo_items"]["basic"].get("copyright")
        copyright = " &copy; " + copyright if copyright is not None else ""
        content = (
            add_figure(image, data["promo_items"]["basic"].get("caption") + copyright)
            + content
        )
        
        audio = get_audio_url(url)
        if audio.get("status") == "DONE":
            content = f"<audio controls src=\"{audio['audio_url']}\"></audio>"  + content

        super().__init__(
            id=article_id,
            headline=data["headlines"]["basic"],
            subheadline=data["subheadlines"]["basic"],
            content=content,
            url=url,
            image=image,
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)


if __name__ == "__main__":
    article = LiberationArticle.get_from_url(
        "https://www.liberation.fr/sports/football/zidane-nouveau-selectionneur-de-lequipe-de-france-une-oeuvre-de-patience-et-un-effet-retard-20260728_XJNJUDMOGNHT3MBMVYYJU374XE/"
    )

    print(article)
