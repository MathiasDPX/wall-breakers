import re

import requests
from bs4 import BeautifulSoup

from .exceptions import sentry_block_error
from .common import Article, add_figure, fix_links

_URL_ID_PATTERN = re.compile(
    r".+lexpress\.fr\/.+-([A-Z0-9]{26})(?:.+)?"
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
        level = block["level"]
        return f"<h{level}>" + _sanitize_html(block["content"]) + f"</h{level}>"
    elif typename == "link_list":
        # read also
        return ""
    
    sentry_block_error(typename)
    return ""

class ExpressArticle(Article):
    SLUG = "lx"
    PROVIDER = "L'Express"
    FAVICON = "https://www.lexpress.fr/pf/resources/icons/fav/apple-touch-icon.png?d=865"

    def __init__(self, article_id: str):
        data = ExpressArticle.get_data(article_id)

        content = ""
        for block in data["content_elements"]:
            content += _build_block(block)

        # Add image
        content = add_figure(data["promo_items"]["basic"]["url"], data["promo_items"]["basic"].get("caption")) + content

        super().__init__(
            id=data["_id"],
            headline=data["headlines"]["basic"],
            subheadline=data["subheadlines"]["basic"],
            content=content,
            url="https://www.lexpress.fr"+data["website_url"],
            image=data["promo_items"]["basic"]["url"]
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None
        
        return match.group(1)
        
    def get_data(id):
        # Using Android app api key
        r = requests.get(
            f"https://www.lexpress.fr/arc/outboundfeeds/mobile/v1/article/{id}/?token=354e2674f3f34fcc9886d55fd8602a2b"
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = ExpressArticle.get_from_url(
        "https://www.lexpress.fr/idees-et-debats/bernard-legras-cleopatre-etait-une-grande-cheffe-detat-avec-une-veritable-vision-politique-SQ6GWEXB6BGT7ORIXFHP7OJK5U/"
    )

    print(article)