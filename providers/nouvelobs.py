import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

from .common import Article, fix_links

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.nouvelobs\.com\/.+\/(\d{8}.OBS\d+)\/.+\.html"
)


def fix_cri_uri(uri: str):
    if not uri.startswith("crifr://"):
        return uri
        
    if uri.startswith("crifr://open-url"):
        parameters = uri.split("&")
        for parameter in parameters:
            if parameter.startswith("url="):
                return unquote(parameter[4:])
    
    return uri


class NouvelObsArticle(Article):
    SLUG = "no"
    PROVIDER = "Le Nouvel Obs"
    
    def __init__(self, article_id: str):
        data = NouvelObsArticle.get_data(article_id)

        soup = BeautifulSoup(data["templates"]["raw_content"]["content"], features="html.parser")
        if soup.find_all("div", attrs={"class": "article_content"}):
            soup = soup.find("div", attrs={"class": "article_content"})

        illustration = soup.select_one("header.article-header figure img")
        image = illustration.get("src") if illustration else None

        for container in soup.select(".btn, div.recirculating-series, header.highlights, aside, div.article__affiliated-content, div.toast-container, div:not([class]), div.d-flex, div.advertising, div.article__author"):
            container.decompose()
            
        for element in soup.select("p"):
            if element.decode_contents().strip() == "Pour aller plus loin":
                element.decompose()

        # Obliterate document metadata and non-content elements
        for tag in soup.select("head, script, style"):
            if tag.parent is not None:
                tag.decompose()

        for tag in soup.find_all():
            # Keep only allowed attributes
            tag.attrs = {
                key: value
                for key, value in tag.attrs.items()
                if key in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label",)
            }
            
            if (
                not tag.get_text(strip=True)
                and not tag.find()
                and tag.name not in ["img", "br", "hr", "input"]
            ):
                tag.decompose()


        for a in soup.find_all("a", href=True):
            a["href"] = fix_cri_uri(a["href"])
        
        fix_links(soup)

        figure = soup.find("figure")
        if figure:
            img = figure.find("img")
            if img and image is None:
                image = img.get("src")

        content = soup.decode_contents()
        content = content.replace("{{{ scripts_bottom }}}", "")

        super().__init__(
            id=article_id,
            headline=data["element"]["title"],
            subheadline=data["element"]["subtitle"],
            content=content,
            url=data["sharing"]["configurations"]["default"]["url"],
            image=image
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is not None:
            return match.group(1)
        
        return None
    
    def get_data(id):
        r = requests.get(
            f"https://apps.nouvelobs.com/obs/v1/premium-android-phone/article/{id}"
        )
        r.raise_for_status()
        return r.json()
    
    def get_readable_data(id):
        data = NouvelObsArticle.get_data(id)
        return data["templates"]["raw_content"]["content"]


if __name__ == "__main__":
    article = NouvelObsArticle.get_from_url("https://www.nouvelobs.com/monde/20260807.OBS117259/sur-les-traces-d-ulysse-de-troie-a-djerba-nous-reprenons-la-mer-l-ame-navree.html")

    print(article)
