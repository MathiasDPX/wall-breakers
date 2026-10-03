from functools import lru_cache
from datetime import datetime
import base64
import os
import re

from bs4 import BeautifulSoup

from .auth import SocialterClient
from .common import Article, fix_links, add_figure
from .exceptions import SocialterDisabledException, SocialterLayoutError

_URL_ID_PATTERN = re.compile(r"https:\/\/www\.socialter\.fr\/article\/(.+)")

ENABLED = os.getenv("ENABLE_SA", "false").lower() == "true"

if ENABLED:
    client = SocialterClient()
    client.start_refresh_loop()
else:
    client = None

months = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}

def select_or_raise(soup, selector):
    element = soup.select_one(selector)

    if element is None:
        raise SocialterLayoutError(
            f"`{selector}` is missing from the page, Socialter probably changed its layout."
        )

    return element

def select_text(soup, selector, default=""):
    element = soup.select_one(selector)

    return element.get_text().strip() if element is not None else default

def parse_date(full):
    items = full.split()

    try:
        day = int(items[-3])
        month = months[items[-2]]
        year = int(items[-1])

        return datetime(year, month, day)
    except (IndexError, KeyError, ValueError):
        raise SocialterLayoutError(f"Could not read a date out of `{full}`.")

class SocialterArticle(Article):
    SLUG = "sa"
    PROVIDER = "Socialter"
    FAVICON = "https://www.socialter.fr/theme/images/favicon.png"

    def __init__(self, article_id: str):
        if client is None:
            raise SocialterDisabledException()

        data = SocialterArticle.get_data(article_id)
        soup = BeautifulSoup(data, features="html.parser")
        article_path = base64.b64decode(article_id).decode()

        headline = select_or_raise(soup, "div.entry-title").get_text().strip()
        subheadline = select_text(soup, "p.lead")
        image_element = soup.select_one("div.entry-image img")
        image = image_element.get("src", "") if image_element else ""
        image_legend = select_text(soup, "span.entry-image-legend")
        # author is one big element with author and date
        author = select_text(soup, "div.entry-author")
        date = parse_date(author) if author else None

        content = select_or_raise(soup, "div.entry-content")
        
        for elem in soup.select('div.frame-donation, div.postfooter, [style*="text-align: center"]'):
            elem.decompose()
            
        for image in content.select('img'):            
            if not image["src"].startswith("/"):
                continue
            
            image["src"] = "https://www.socialter.fr/" + image["src"]
            
        # Remove empty tags
        for tag in soup.find_all():
            if (
                not tag.get_text(strip=True)
                and not tag.find()
                and tag.name not in ["img", "br", "hr", "input"]
            ):
                tag.decompose()
        
        fix_links(content)
        
        content = content.decode_contents()

        if image:
            content = add_figure(image["src"], image_legend) + content

        super().__init__(
            id=article_id,
            headline=headline,
            subheadline=subheadline,
            content=content,
            url=f"https://www.socialter.fr/article/{article_path}",
            image=image,
            publication_date=date
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return base64.b64encode(match.group(1).encode()).decode("ascii")
    
    @lru_cache(maxsize=64)
    def get_data(id):
        if client is None:
            raise SocialterDisabledException()

        article_path = base64.b64decode(id).decode()
        r = client.get(f"https://www.socialter.fr/article/{article_path}")
        r.raise_for_status()

        return r.content

    @classmethod
    def is_enabled(cls) -> bool:
        return client is not None


if __name__ == "__main__":
    article = SocialterArticle.get_from_url(
        "https://www.socialter.fr/article/christophe-cassou-pourquoi-il-faut-politiser-les-canicules-climat-ete-rassurisme-adaptation"
    )

    print(article)
