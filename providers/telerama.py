import base64
import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

from .common import Article, fix_links

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.telerama\.fr(.+)"
)

_URI_ID_PATTERN = re.compile(
    r"tlrm:\/\/element\?id=(.+).*"
)

class TeleramaArticle(Article):
    SLUG = "tr"
    PROVIDER = "Telerama"
    
    def __init__(self, article_id: str):
        data = TeleramaArticle.get_data(article_id)

        soup = BeautifulSoup(data["templates"]["raw_content"]["content"], features="html.parser")
        subheadline = soup.select_one("p.article__chapeau").decode_contents()
        if soup.find_all("article", attrs={"class": "article__page-content"}):
            soup = soup.find("article", attrs={"class": "article__page-content"})

        illustration = soup.select_one("header.article-header figure img")
        image = illustration.get("src") if illustration else None

        for container in soup.select("noscript, style, script, link, section.article__page-header, p.article__chapeau, ul.sheet__notation-container, section.article__details, section.hide, section.video, section.edito"):
            container.decompose()
            
        for link in soup.select("section.media__lighbox a"):
            link.unwrap()

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
            headline=data["template_vars"]["share_title"],
            subheadline=subheadline,
            content=content,
            url=data["template_vars"]["share_title"],
            image=image
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is not None:
            return base64.b64encode(match.group(1).encode()).decode("ascii")
        
        match = _URI_ID_PATTERN.search(url)
        if match is not None:
            return base64.b64encode(unquote(match.group(1)).encode()).decode("ascii")
        
        return None
    
    def get_data(id):
        article_path = base64.b64decode(id).decode()
        r = requests.get(
            f"https://apps.telerama.fr/tlr/v1/premium-android-phone/element",
            params={"id": article_path}
        )
        r.raise_for_status()
        return r.json()
    
    def get_readable_data(id):
        data = TeleramaArticle.get_data(id)
        return data["templates"]["raw_content"]["content"]


if __name__ == "__main__":
    article = TeleramaArticle.get_from_url("https://www.telerama.fr/series-tv/alley-cats-sur-netflix-ricky-gervais-aux-manettes-d-une-serie-animee-feline-et-chat-nous-plait-bien_cri-7045364.php")

    print(article)
