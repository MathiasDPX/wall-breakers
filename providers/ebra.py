import re

from functools import lru_cache
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure, fix_links

_ID_PATTERN = re.compile(
    r'<meta name="ArticleId" content="([a-z0-9-]{36})"'
)

_PATH_PATTERN = re.compile(
    r"\/[a-z0-9-]+\/\d{4}\/\d{2}\/\d{2}\/.+"
)

_URL_IN_CONTENT_PATTERN = re.compile(
    r'"click_url": "(%[a-zA-Z0-9._%-]+)'
)

class EbraArticle(Article):
    DOMAIN = None
    APP = None

    def __init__(self, article_id: str):
        data = self.get_data(article_id)
        metadata = data["metadata"]
        detail = metadata["detail"]

        image = detail.get("image") or next(iter(detail.get("images") or []), None)

        if detail.get("components"):
            # Unpaid articles come as a list of components
            content = "".join(component["html"] for component in detail["components"])
        else:
            # Paid articles are fully available in the services endpoint
            soup = BeautifulSoup(data["html"], features="html.parser")
            body = soup.select_one(".retrievedBodyContent")
            content = body.decode_contents() if body else ""

        if image:
            content = add_figure(image["url"], image["descriptionHtml"]) + content

        soup = BeautifulSoup(content, features="html.parser")
        
        for element in soup.select(".fullDetailActions"):
            element.decompose()
        
        for tag in soup.find_all():
            # Obliterate unwanted tags
            if tag.name in ("script", "style", "link"):
                tag.decompose()
                continue

            # Keep only allowed attributes
            tag.attrs = {
                key: value
                for key, value in tag.attrs.items()
                if key in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label",)
            }
        
        fix_links(soup)
        
        super().__init__(
            id=article_id,
            headline=metadata["title"],
            subheadline=detail.get("standfirst") or "",
            content=soup.decode_contents(),
            url=metadata["weburl"],
            image=image["url"] if image else "static/images/thumbnail.jpg"
        )
    
    @classmethod
    @lru_cache()
    def get_id_from_url(cls, url: str):
        parsed = urlparse(url)
        
        if parsed.netloc.removeprefix("www.") != cls.DOMAIN.removeprefix("www."):
            return None
        
        if _PATH_PATTERN.fullmatch(parsed.path) is None:
            return None
        
        r = requests.get(url)
        r.raise_for_status()
        article_id = _ID_PATTERN.search(r.content.decode())
        
        if article_id is None:
            return None
        
        return article_id.group(1)
    
    @classmethod
    def get_data(cls, article_id: str):
        content_response = requests.get(f"https://{cls.DOMAIN}/services/grdc/detail?key={article_id}")
        content_response.raise_for_status()
        content_data = content_response.json()["html"]
        
        match = _URL_IN_CONTENT_PATTERN.search(content_data)
        
        if match is None:
            raise ValueError(f"No article path found for {article_id} on {cls.DOMAIN}")
        
        url = match.group(1)
        
        url = re.sub(r"%252f", "%2F", url, flags=re.IGNORECASE)
        
        metadata_response = requests.get(
            f"https://{cls.DOMAIN}/app_mobile/grdc/detail"
            + "?url=" + url + "&_media=AN&app=" + cls.APP
        )
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        
        return {
            "html": content_data,
            "metadata": metadata["result"]
        }

class JSLArticle(EbraArticle):
    SLUG = "jsl"
    PROVIDER = "Le Journal de Saône-et-Loire"
    FAVICON = "https://cdn-files.prsmedia.fr/files/REDAC/images/favicons/2022/favicon_JSL-V2.png"
    
    DOMAIN = "www.lejsl.com"
    APP = "JSL"

class DNAArticle(EbraArticle):
    SLUG = "dna"
    PROVIDER = "Dernières Nouvelles d'Alsace"
    FAVICON = "https://cdn-files.prsmedia.fr/files/REDAC/images/favicons/2022/favicon_DNA-V2.png"
    
    DOMAIN = "www.dna.fr"
    APP = "DNA"

class DaupineArticle(EbraArticle):
    SLUG = "ld"
    PROVIDER = "Le Dauphiné Libéré"
    FAVICON = "https://cdn-files.prsmedia.fr/files/REDAC/images/favicons/2022/favicon_LDL-V2.png"
    
    DOMAIN = "www.ledauphine.com"
    APP = "LDL"

class EstRepuArticle(EbraArticle):
    SLUG = "er"
    PROVIDER = "L'Est Républicain"
    FAVICON = "https://cdn-files.prsmedia.fr/files/REDAC/images/favicons/2022/favicon_LER-V2.png"
    
    DOMAIN = "www.estrepublicain.fr"
    APP = "LER"

class RepuLorrainArticle(EbraArticle):
    SLUG = "rl"
    PROVIDER = "Le Républicain Lorrain"
    FAVICON = "https://cdn-files.prsmedia.fr/files/REDAC/images/favicons/2022/favicon_LRL-V2.png"
    
    DOMAIN = "www.republicain-lorrain.fr"
    APP = "LRL"

class BienPublicArticle(EbraArticle):
    SLUG = "bp"
    PROVIDER = "Le Bien Public"
    FAVICON = "https://cdn-files.prsmedia.fr/files/REDAC/images/favicons/2022/favicon_LBP-V2.png"
    
    DOMAIN = "www.bienpublic.com"
    APP = "LBP"

class VosgesMatinArticle(EbraArticle):
    SLUG = "vm"
    PROVIDER = "Vosges Matin"
    FAVICON = "https://cdn-files.prsmedia.fr/files/REDAC/images/favicons/2022/favicon_VOM-V2.png"
    
    DOMAIN = "www.vosgesmatin.fr"
    APP = "VOM"

class ProgresArticle(EbraArticle):
    SLUG = "lpr"
    PROVIDER = "Le Progrès"
    FAVICON = "https://cdn-files.prsmedia.fr/files/REDAC/images/favicons/2022/favicon_LPR-V2.png"
    
    DOMAIN = "www.leprogres.fr"
    APP = "LPR"

class AlsaceArticle(EbraArticle):
    SLUG = "als"
    PROVIDER = "L'Alsace"
    FAVICON = "https://cdn-files.prsmedia.fr/files/REDAC/images/favicons/2022/favicon_ALS-V2.png"
    
    DOMAIN = "www.lalsace.fr"
    APP = "ALS"


if __name__ == "__main__":
    article = JSLArticle.get_from_url("https://www.lejsl.com/economie/2026/08/24/un-duo-mere-fille-ouvre-une-boutique-de-seconde-main-pour-enfants")

    print(article)
