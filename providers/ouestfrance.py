import os
import re

from bs4 import BeautifulSoup

from .common import Article, OAuthClient, add_figure, fix_links, make_figcaption
from .exceptions import *

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.ouest-france\.fr\/.+-([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})"
)

REFRESH_TOKEN = os.getenv("OUESTFRANCE_REFRESH_TOKEN", None)

if REFRESH_TOKEN:
    client = OAuthClient(
        REFRESH_TOKEN,
        os.getenv("OUESTFRANCE_AZP", "bms-sso-login"),
        "https://auth.ouest-france.fr/auth/realms/sipa/protocol/openid-connect/token"
    )
    client.start_refresh_loop()
else:
    client = None

def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    
    fix_links(soup)
    
    return soup.decode_contents()

def _build_block(block):
    typename = block["type"]
    
    if typename == "TEXT_PARAGRAPH":
        lowercase = block["data"]["content"].lower()
        if "lire aussi" in lowercase and "<strong>" in lowercase:
            return ""
        
        return "<p>" + _sanitize_html(block["data"]["content"]) + "</p>"
    elif typename == "TEXT_HEADING":
        hlevel = block["data"]["level"]
        return f"<h{hlevel}>" + block["data"]["content"] + f"</h{hlevel}>"
    
    return ""

class OuestFranceArticle(Article):
    SLUG = "of"
    PROVIDER = "Ouest-France"
    FAVICON = "https://media.ouest-france.fr/v1/pictures/c1e53b40060544ad069e9bcb80c1695e-apple-touch-icon.png?client_id=cmsfront&sign=65ca41798b5fc22da12dea1b06dbd34f69c2ae1362fd347f463b9146393e92c0"

    def __init__(self, article_id: str):
        if not REFRESH_TOKEN:
            raise OuestFranceDisabledException()
        
        data = OuestFranceArticle.get_data(article_id)["data"]

        # paying: is the article for subscribers only
        # paid: does the user has a subscription
        # paid is false if paying is, even if the user has an active subscription
        if data["paywall"]["paid"] != data["paywall"]["paying"]:
            raise OuestFranceMissingSubscriptionException()

        image = data["photos"][0]

        content = add_figure(image["url"], make_figcaption(image['caption'], image['credits']))

        for block in data["body"]:
            content += _build_block(block)

        super().__init__(
            id=article_id,
            headline=data["title"],
            subheadline=data["lead"],
            content=content,
            url=data["url"],
            image=image["url"],
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)
    
    def get_data(id):
        r = client.get("https://api-device.ouest-france.fr/app/OF/v1/contents/"+id)
        
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = OuestFranceArticle.get_from_url("https://www.ouest-france.fr/societe/ruralites/tu-es-un-peu-le-maire-sans-lecharpe-les-secretaires-de-mairie-espece-en-voie-de-disparition-1b28e6b2-66d4-11f0-bb8e-c5b2af864a8a")

    print(article)
