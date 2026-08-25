import re
import json
from functools import lru_cache

from bs4 import BeautifulSoup
import requests

from .common import Article, add_figure, fix_links

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.scmp\.com\/.+\/article\/(\d+)\/.+"
)

_UUID_PATTERN = re.compile(
    r'"entityId":"\d+","entityUuid":"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})"'
)

_HEADERS = {
    "User-Agent": "SCMP-V5/7.2.1(2000386) (Android 9; HD1900)",
    "Accept": "application/json",
    "apiKey": "MyYvyg8M9RTaevVlcIRhN5yRIqqVssNY",
    "Apollo-Require-Preflight": "true"
}

def _build_block(block):
    typename = block["type"]
    
    if typename == "p":
        return "<p>" + _build_blocks(block["children"]) + "</p>"
    elif typename == "div":
        return "<div>" + _build_blocks(block["children"]) + "</div>"
    elif typename == "text":
        return block["data"]
    elif typename == "a":
        attrs = " ".join([f"{k}=\"{v}\"" for k,v in block.get("attribs", {}).items()])
        subchildren = _build_blocks(block["children"])
        return f"<a {attrs}>{subchildren}</a>"
    elif typename == "img":
        attrs = " ".join([f"{k}=\"{v}\"" for k,v in block.get("attribs", {}).items()])
        return f"<img {attrs}>"
    elif typename == "iframe":
        attrs = " ".join([f"{k}=\"{v}\"" for k,v in block.get("attribs", {}).items()])
        return f"<iframe {attrs}></iframe>"
    
    return ""

def _build_blocks(blocks):
    content = ""
    for block in blocks:
        content += _build_block(block)
        
    return content

class SCMPArticle(Article):
    SLUG = "scmp"
    PROVIDER = "South China Morning Post"
    FAVICON = "https://assets-v2.i-scmp.com/production/icons/scmp-icon-256x256.png"

    def __init__(self, article_id: str):
        data = SCMPArticle.get_data(article_id)

        content = _build_blocks(data["body"]["json"])
        
        if len(data["images"]) > 0:
            image = data["images"][0]
            if image.get("isSlideshow"):
                content = add_figure(image["url"], title=image.get("title", "")) + content
                
        soup = BeautifulSoup(content, features="html.parser")
        fix_links(soup)

        super().__init__(
            id=article_id,
            headline=data["headline"],
            subheadline=_build_blocks(data["subHeadline"]["json"]),
            content=soup.decode_contents(),
            url="https://www.scmp.com"+data["urlAlias"],
            image=image["url"]
        )
        
    @lru_cache()
    def _get_uuid(url:str):
        r = requests.get(url)
                
        match = _UUID_PATTERN.search(r.content.decode())
        if match is None:
            return None
                
        return match.group(1)
    
    def get_id_from_url(url: str):
        if _URL_ID_PATTERN.search(url) is None:
            return None
        
        return SCMPArticle._get_uuid(url)
    
    def get_data(id):
        url = "https://apigw.scmp.com/content-delivery/v2"

        params = {
            "operationName": "ArticleDetailQuery",
            "variables": json.dumps({
                "entityUuid": id,
                "contentType": "ARTICLE",
                "customContents": []
            }, separators=(",", ":")),
            "extensions": json.dumps({
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "328928987b3d5a3b5fbeaedbb98c046cb7515dc363fe808bfb6710051e0c03ff"
                },
                "clientLibrary": {
                    "name": "apollo-kotlin",
                    "version": "5.0.1"
                }
            }, separators=(",", ":"))
        }
        r = requests.get(url, params=params, headers=_HEADERS)
        r.raise_for_status()
        return r.json()["data"]["content"]


if __name__ == "__main__":
    article = SCMPArticle.get_from_url(
        "https://www.scmp.com/news/china/military/article/3365081/mainland-chinas-ship-activity-near-taiwan-hits-record-third-month-row?module=top_story&pgtype=homepage"
    )

    print(article)