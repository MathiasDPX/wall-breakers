import re
import os
import base64

from flask import redirect
from bs4 import BeautifulSoup

from .exceptions import MediapartDisabledException
from .common import Article, CASClient, fix_links

_URL_ID_PATTERN = re.compile(
    r"(https:\/\/www\.mediapart\.fr\/.+\/\d+\/.+)"
)

PIERREVIVES_USERNAME = os.getenv("PIERREVIVES_USERNAME")
PIERREVIVES_PASSWORD = os.getenv("PIERREVIVES_PASSWORD")

if PIERREVIVES_USERNAME and PIERREVIVES_PASSWORD:
    client = CASClient(
        PIERREVIVES_USERNAME,
        PIERREVIVES_PASSWORD,
    )
    client.start_refresh_loop()
else:
    client = None

class MediapartArticle(Article):
    SLUG = "mp"
    PROVIDER = "Mediapart"
    FAVICON = "https://www.mediapart.fr/icon-news.svg"
    
    def __init__(self, article_id: str):
        if client == None:
            raise MediapartDisabledException()
        
        data = MediapartArticle.get_data(article_id)

        soup = BeautifulSoup(data, features="html.parser")
        content_soup = soup.find("main", class_="news__body-wrapper")

        headline = soup.select_one("h1#page-title").decode_contents()
        subheadline = soup.find("p", class_="news__heading__top__intro").decode_contents()
        url = soup.find("meta", property="og:url").get("content")
        image = soup.find("meta", property="og:image").get("content")

        selectors = [
            'div.news__heading',
            'div.splitter',
            'time',
            'span[aria-hidden="true"]',
            'svg.media-container__fallback-icon',
            'aside:not([class])',
            'div.news__signature',
            'p.left, p.right, p.center',
            'div.hidden',
            'aside.news__body__right',
            'aside.read-also',
            'article.collection-card',
            'div.news__body__center__bottom',
            'a.news__prolonger',
            'aside.box._source'
        ]
        for container in content_soup.select(", ".join(selectors)):
            for video in container.select("figure.media--video"):
                container.insert_before(video.extract())
            for video in container.select("video, iframe"):
                container.insert_before(video.extract())
            container.decompose()

        content_soup.find("div", class_="news__body").unwrap()

        # Keep all attributes for descendants of Vimeo figures
        vimeo_descendants = {id(d) for f in soup.select("figure[data-path*='player.vimeo.com']") for d in f.find_all()}

        for tag in soup.find_all():
            # Obliterate unwanted tags
            if tag.name in ("script", "style", "link"):
                tag.decompose()
                continue
            
            if "media--video__iframe-wrapper" in tag.get("class", []):
                tag.attrs = {}

            # Don't strip attributes inside Vimeo figures
            if id(tag) in vimeo_descendants:
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
                and tag.name not in ["img", "br", "hr", "input", "iframe", "video", "audio", "source"]
            ):
                tag.decompose()

        for iframe in soup.select("figure[data-path*='player.vimeo.com'] iframe"):
            w = iframe.get("width", "")
            h = iframe.get("height", "")
            ratio = "16 / 9"
            try:
                if int(w) > 0 and int(h) > 0:
                    ratio = f"{int(w)} / {int(h)}"
            except (ValueError, TypeError):
                pass
            iframe.attrs.pop("width", None)
            iframe.attrs.pop("height", None)
            iframe.attrs.pop("style", None)
            iframe["style"] = f"aspect-ratio: {ratio};"

        fix_links(soup)

        super().__init__(
            id=article_id,
            headline=headline,
            subheadline=subheadline,
            content=content_soup.decode_contents(),
            url=url,
            image=image
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None
        
        return base64.b64encode(match.group(1).encode()).decode("ascii")
    
    def get_data(id):
        article_path = base64.b64decode(id)
        r = client.get(article_path)
        r.raise_for_status()
        
        return r.content
    
    def get_readable_data(id):
        return redirect("./raw")


if __name__ == "__main__":
    article = MediapartArticle.get_from_url("https://www.mediapart.fr/journal/international/020826/les-jours-comptes-de-gianni-infantino-la-tete-du-football-mondial")

    print(article)
