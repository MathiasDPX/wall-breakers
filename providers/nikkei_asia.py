import re
import json
import base64

from bs4 import BeautifulSoup
import requests

from .common import Article, fix_links, add_figure

_URL_ID_PATTERN = re.compile(
    r"https:\/\/asia\.nikkei\.com(\/.+)"
)

class NikkeiAsiaArticle(Article):
    SLUG = "na"
    PROVIDER = "Nikkei Asia"
    FAVICON = "https://asia.nikkei.com/images/frontend/favicons/288x288.png"

    def __init__(self, article_id: str):
        data = NikkeiAsiaArticle.get_data(article_id)

        soup = BeautifulSoup(data["body"], features="html.parser").find("body")
        
        for tag in soup.find_all():
            if tag.name == "svg":
                tag.decompose()
                continue
            
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
            
        for tag in soup.select("div > div"):
            # Replace Nikkei Asia figures with custom figures
            image = tag.select_one("img")
            if image is None:
                continue
            
            span = soup.select_one("span")
            if span is None:
                span = ""
            else:
                span = span.decode_contents()
            
            tag.replace_with(BeautifulSoup(add_figure(image.get("src"), span), features="html.parser"))
        
        
        
        fix_links(soup)
        content = soup.decode_contents()

        super().__init__(
            id=article_id,
            headline=data["headline"],
            subheadline=data["subhead"],
            content=content,
            url=data["url"],
            image=data["image"]["imageUrl"],
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return base64.b64encode(match.group(1).encode()).decode("ascii")
    
    def get_data(id):
        article_path = base64.b64decode(id).decode()
        
        params = {
            "operationName": "GetPage",
            "variables": json.dumps({
                "url": article_path
            }),
            "extensions": json.dumps({
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "b4f049bbb47782a540a2df37107d7d74b36b41bb1f3017ae6f6387fad18efacd"
                }
            })
        }
        
        r = requests.get(
            "https://asia.nikkei.com/api/__service/next_api/v1/graphql",
            params=params,
            headers={
                "Content-Type": "application/json"
            }
        )
        
        r.raise_for_status()
        return r.json()["data"]["getPage"]


if __name__ == "__main__":
    article = NikkeiAsiaArticle.get_from_url("https://www.ft.com/content/32a70a3c-7d28-40b4-808e-36edb58c7d01")
    
    print(article)
