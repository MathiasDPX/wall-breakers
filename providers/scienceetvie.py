import re

import requests
from bs4 import BeautifulSoup, NavigableString

from .common import Article, add_figure, fix_links

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.science-et-vie\.com\/.+-(\d+)\.html"
)

_YOUTUBE_ID_PATTERN = re.compile(r"(?:youtu\.be\/|[?&]v=)([a-zA-Z0-9_-]{11})")


def _adjacent_tag(tag, forward):
    for sibling in (tag.next_siblings if forward else tag.previous_siblings):
        if isinstance(sibling, NavigableString):
            if sibling.strip():
                return None
            continue
        return sibling

    return None


def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")

    for player in soup.select("div.jwplayer"):
        img_player = _adjacent_tag(player, forward=False)
        if img_player is not None and img_player.name == "div" and "img_player" in img_player.get("class", []):
            img_player.decompose()

        script = _adjacent_tag(player, forward=True)
        video_id = None
        if script is not None and script.name == "script":
            match = _YOUTUBE_ID_PATTERN.search(script.get_text())
            if match is not None:
                video_id = match.group(1)
            script.decompose()

        if video_id is not None:
            iframe = soup.new_tag("iframe", src=f"https://www.youtube.com/embed/{video_id}", frameborder="0")
            player.replace_with(iframe)
        else:
            player.decompose()

    for script in soup.find_all("script"):
        script.decompose()

    for tag in soup.find_all():
        if (
            not tag.get_text(strip=True)
            and not tag.find()
            and tag.name not in ["img", "br", "hr", "input", "iframe"]
        ):
            tag.decompose()

    for tag in soup.find_all():
        # Keep only allowed attributes
        tag.attrs = {
            key: value
            for key, value in tag.attrs.items()
            if key in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label", "frameborder",)
        }

    fix_links(soup)

    return soup.decode_contents()


class ScienceEtVieArticle(Article):
    SLUG = "sev"
    PROVIDER = "Science et Vie"
    FAVICON = "https://www.science-et-vie.com/wp-content/themes/scienceetvie-v2/assets/images/favicons/favicon128.png"

    def __init__(self, article_id: str):
        data = ScienceEtVieArticle.get_data(article_id)

        image = data.get("featured_image")

        content = ""
        if image:
            content += add_figure(image["media"], image.get("copyright"))
        content += _sanitize_html(data["content"]["rendered"])

        subheadline = BeautifulSoup(data["excerpt"]["rendered"], features="html.parser").get_text(strip=True)

        super().__init__(
            id=article_id,
            headline=data["title"]["rendered"],
            subheadline=subheadline,
            content=content,
            url=data["link"],
            image=image["media"] if image else None,
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)

    def get_data(id):
        r = requests.get(f"https://www.science-et-vie.com/wp-json/wp/v2/posts/{id}", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        })
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = ScienceEtVieArticle.get_from_url("https://www.science-et-vie.com/corps-et-sante/cancer/une-seule-boisson-sucree-par-jour-pourrait-augmenter-de-145-le-risque-de-cancer-de-lestomac-257643.html")

    print(article)
