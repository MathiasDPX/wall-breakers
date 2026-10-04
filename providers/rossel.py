import re
from datetime import datetime

from bs4 import BeautifulSoup
import requests

from .common import Article, fix_links

_ID_PATTERN = re.compile(r"\/(?:id)?(\d+)\/article\/\d{4}-\d{2}-\d{2}\/.+")

# Ads come either as the legacy <r-pub>/<i-pub> pair or as a <div class="gr-ads-inread"> on
# the most recent sites. Related-stories blocks are dropped too, they are not article content.
_UNWANTED_SELECTORS = "aside.r-stories, div.gr-linked-stories, r-pub, i-pub, div.gr-ads-inread"

_DEFAULT_IMAGE = "static/images/thumbnail.jpg"


def _get_image(data: dict, soup: BeautifulSoup) -> str:
    """URL of the lead image, from the image object of the article or from its first inline image.

    The "default" crop is stale (404) on every site, the named ones ("ena_16_9_big", ...) are live.
    """
    crops = {}

    for definition in (data.get("object_definitions") or {}).values():
        if isinstance(definition, dict) and definition.get("type") == "image":
            crops.update({
                name: (crop or {}).get("url") or ""
                for name, crop in (definition.get("crop_definitions") or {}).items()
            })

    image = soup.find("img") or {}
    srcset = image.get("srcset") or ""
    inline = image.get("src") or srcset.split(",")[0].strip().split(" ")[0]

    candidates = [*(url for name, url in crops.items() if name != "default"), inline]

    for candidate in candidates:
        if candidate and candidate.startswith("http"):
            return candidate

    return _DEFAULT_IMAGE


class RosselArticle(Article):
    GROUP = "Groupe Rossel"
    DOMAIN = None
    API_EXTRA = "_cp"

    def __init__(self, article_id: str):
        data = self.get_data(article_id)
        
        content = data["body"]
        soup = BeautifulSoup(content, features="html.parser")
        
        for elem in soup.select(_UNWANTED_SELECTORS):
            elem.decompose()
        
        # Remove empty tags
        for tag in soup.find_all():
            # Remove empty tags
            if (
                not tag.get_text(strip=True)
                and not tag.find()
                and tag.name not in ["img", "br", "hr", "input"]
            ):
                tag.decompose()
                continue
            
            # Keep only allowed attributes
            tag.attrs = {
                key: value
                for key, value in tag.attrs.items()
                if key in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label",)
            }
            
        fix_links(soup)

        image = _get_image(data, soup)

        # Timestamps are strings in the API payload
        publication_date = data.get("pubDate") or data.get("creationDate")

        super().__init__(
            id=article_id,
            headline=data.get("title", ""),
            subheadline=data.get("chapo_stripped", ""),
            content=soup.decode_contents(),
            url="https://"+data.get("canonical_url", ""),
            image=image,
            publication_date=datetime.fromtimestamp(int(publication_date)) if publication_date else None
        )
    
    @classmethod
    def get_id_from_url(cls, url: str):
        if not url.startswith("https://"+cls.DOMAIN):
            return None
        
        article_id = _ID_PATTERN.search(url)
        
        if article_id is None:
            return None
        
        return article_id.group(1)
    
    @classmethod
    def get_data(cls, article_id: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:157.0) Gecko/20100101 Firefox/157.0"
        }
        response = requests.get(f"https://{cls.DOMAIN}/api/article/apps{cls.API_EXTRA}/{article_id}.json", headers=headers)
        response.raise_for_status()
        data = response.json()
        
        return data

class VDNArticle(RosselArticle):
    SLUG = "vdn"
    PROVIDER = "La Voix du Nord"
    FAVICON = "https://lvdneng.rosselcdn.net/sites/default/files/mediastore/1590671347_pwa-192.png"
    
    DOMAIN = "www.lavoixdunord.fr"

class LeMessagerArticle(RosselArticle):
    SLUG = "lmsg"
    PROVIDER = "Le Messager"
    FAVICON = "https://phrmeseng.rosselcdn.net/sites/all/themes/enacarbon_lemessager/favicon.ico"
    
    DOMAIN = "www.lemessager.fr"
    
class LeSoirArticle(RosselArticle):
    SLUG = "ls"
    PROVIDER = "Le Soir"
    FAVICON = "https://play-lh.googleusercontent.com/R7O7eyXpxdqz4JQAF6kDoOkNwm8QVApR1AhWWpN3nTdDdCss3phDXztvpxEt4LpMhlOJk_cg4d7VJ6S3VsLg"
    
    DOMAIN = "www.lesoir.be"

class NordLittArticle(RosselArticle):
    SLUG = "nl"
    PROVIDER = "Nord Littoral"
    FAVICON = "https://phrnleng.rosselcdn.net/sites/default/files/nlg_icon_0.png"
    
    DOMAIN = "www.nordlittoral.fr"

class ParisNormandieArticle(RosselArticle):
    SLUG = "pn"
    PROVIDER = "Paris Normandie"
    FAVICON = "https://play-lh.googleusercontent.com/rZiZM0XT49u3YJ0ttzHJGJXYps6W44XRHEzJxzzPpqPfOwTjjij3b6Hcy2ZIVxRSo2NVw16ksrwitnCug3vjReg"
    
    DOMAIN = "www.paris-normandie.fr"
    
class SudInfoArticle(RosselArticle):
    SLUG = "si"
    PROVIDER = "SudInfo"
    FAVICON = "https://www.sudinfo.be/sites/default/files/mediastore/1655376696_icon_192x192.png"
    
    DOMAIN = "www.sudinfo.be"

class CourrierPicardArticle(RosselArticle):
    SLUG = "cp"
    PROVIDER = "Courrier Picard"
    FAVICON = "https://prmeng.rosselcdn.net/sites/all/themes/enacarbon_cp/favicon.ico"
    
    DOMAIN = "www.courrier-picard.fr"
    API_EXTRA = "_cp"

class AisneNouvelleArticle(RosselArticle):
    SLUG = "an"
    PROVIDER = "Aisne Nouvelle"
    FAVICON = "https://prmeng.rosselcdn.net/sites/all/themes/enacarbon_an/favicon.ico"
    
    DOMAIN = "www.aisnenouvelle.fr"
    API_EXTRA = "_an"
    
class ArdennaisArticle(RosselArticle):
    SLUG = "ar"
    PROVIDER = "L'Ardennais"
    FAVICON = "https://remeng.rosselcdn.net/sites/all/themes/enacarbon_ard/favicon.ico"
    
    DOMAIN = "www.lardennais.fr"
    API_EXTRA = "_ar"

class EstEclairArticle(RosselArticle):
    SLUG = "ee"
    PROVIDER = "L'Est éclair"
    FAVICON = "https://remeng.rosselcdn.net/sites/all/themes/enacarbon_ee/favicon.ico"
    
    DOMAIN = "www.lest-eclair.fr"
    API_EXTRA = "_ee"

class LibChampagneArticle(RosselArticle):
    SLUG = "lc"
    PROVIDER = "Liberation Champagne"
    FAVICON = "https://remeng.rosselcdn.net/sites/all/themes/enacarbon_lc/favicon.ico"
    
    DOMAIN = "www.liberation-champagne.fr"
    API_EXTRA = "_lc"
    
class UnionArticle(RosselArticle):
    SLUG = "un"
    PROVIDER = "L'Union"
    FAVICON = "https://remeng.rosselcdn.net/sites/all/themes/enacarbon_uni/favicon.ico"
    
    DOMAIN = "www.lunion.fr"
    API_EXTRA = "_un"

if __name__ == "__main__":
    article = VDNArticle.get_from_url("https://www.lavoixdunord.fr/1742999/article/2026-10-03/personne-n-imagine-le-travail-colossal-qu-il-y-derriere-ces-benevoles-qui")

    print(article)
