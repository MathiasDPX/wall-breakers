from urllib.parse import urlparse, urlunparse
import base64
import re

from bs4 import BeautifulSoup
import requests

from .common import Article, add_figure

_URL_ID_PATTERN = re.compile(r"(https:\/\/www\.washingtonpost\.com/.+)")


def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    
    for link in soup.find_all("a", href=True):
        id = WashingtonPostArticle.get_id_from_url(link["href"])
        link["target"] = "_blank"
        
        if link["href"].startswith("FTS_"):
            link.unwrap()
        
        if id != None:
            link["href"] = "/wp/" + id
            continue
        
        if link["href"].startswith("https://www.amazon."):
            # Remove marketing/tracking parameters
            parsed = urlparse(link["href"])
            clean_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                "",  # params
                "",  # query
                ""   # fragment
            ))
            link["href"] = clean_url
            
    return soup.decode_contents()

def _build_block(block):
    typename = block.get("type")
    
    if typename == "image":
        return add_figure(block['imageURL'], caption=block['fullcaption'], title=block["blurb"])
    elif typename == "sanitized_html":
        return "<p>" + _sanitize_html(block["content"]) + "</p>"
    
    return ""


class WashingtonPostArticle(Article):
    SLUG = "wp"
    PROVIDER = "Washington Post"
    
    def __init__(self, article_id: str):
        article_path = base64.b64decode(article_id).decode()
        
        r = requests.get(
            f"https://rainbowapi-a.wpdigital.net/rainbow-data-service/rainbow/content-by-url.json", params={"url": article_path+"&platform=iphoneclassic&followLinks=false"}
        )
        
        r.raise_for_status()
        data = r.json()

        content = ""
        for block in data["items"]:
            content += _build_block(block)

        super().__init__(
            id=article_id,
            headline=data["title"],
            subheadline=data["blurb"],
            content=content,
            url=article_path,
            image=data["socialImage"]
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return base64.b64encode(match.group(1).encode()).decode("ascii")


if __name__ == "__main__":
    article = WashingtonPostArticle.get_from_url("https://www.washingtonpost.com/opinions/2026/07/26/christopher-nolan-odyssey-shows-cost-online-rage/")

    print(article)
