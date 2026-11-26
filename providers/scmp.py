import re
import json
from datetime import datetime
from functools import lru_cache

from bs4 import BeautifulSoup
import requests

from .exceptions import ArticleNotFoundError, sentry_block_error
from .common import Article, add_figure, fix_links
from metrics import upstream_request_timer

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.scmp\.com\/.+\/article\/(\d+)\/.+"
)

_HEADERS = {
    "User-Agent": "SCMP-V5/7.2.1(2000386) (Android 9; HD1900)",
    "Accept": "application/json",
    "apiKey": "MyYvyg8M9RTaevVlcIRhN5yRIqqVssNY",
    "Apollo-Require-Preflight": "true"
}

def _build_block(block):
    typename = block["type"]
    
    if typename == "text":
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
    elif typename == "blockquote-quote":
        subchildren = "<br>".join([_build_block(subblock) for subblock in block["children"]])
        return f"<blockquote>{subchildren}</blockquote>"
    elif typename in ["strong", "h3", "span", "h4", "em", "ul", "li", "div", "p", "h2", "u", "h5", "hr", "b", "i", "br", "ul", "li", "blockquote"]:
        return f"<{typename}>" + _build_blocks(block.get("children", [])) + f"</{typename}>"
    elif typename in ["meta", "script"]:
        return ""
    
    sentry_block_error(typename)
    
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
        
        if len(data["articleSpeeches"]) > 0:
            voice = data["articleSpeeches"][0]
            content = f"<audio controls src=\"{voice['url']}\"></audio>" + content
        
        image = None
        if len(data["images"]) > 0:
            image = data["images"][0]
            if image.get("isSlideshow"):
                content = add_figure(image["url"], title=image.get("title", "")) + content
                
        soup = BeautifulSoup(content, features="html.parser")
        fix_links(soup)

        date = data.get("publishedDate")

        super().__init__(
            id=article_id,
            headline=data["headline"],
            subheadline=_build_blocks(data["subHeadline"]["json"]),
            content=soup.decode_contents(),
            url="https://www.scmp.com"+data["urlAlias"],
            image=image["url"] if image else None,
            publication_date=datetime.fromtimestamp(date/1000) if date else None
        )
        
    @lru_cache()
    def _get_uuid(article_id: str):
        url = "https://apigw.scmp.com/content-delivery/v2"

        params = {
            "operationName": "Search",
            "variables": json.dumps({
                "keywords": article_id,
                "orderByField": "RELEVANCE",
                "limit": 20
            }, separators=(",", ":")),
            "extensions": json.dumps({
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "626c745700484c1c945ba9f44c36ce66da51dadf59cb8353abe86e4d96b29f7b"
                },
                "clientLibrary": {
                    "name": "apollo-kotlin",
                    "version": "5.0.1"
                }
            }, separators=(",", ":"))
        }
        r = requests.get(url, params=params, headers=_HEADERS, timeout=30)
        r.raise_for_status()

        for edge in r.json()["data"]["articleSearch"]["edges"]:
            content = edge["node"]["articleContent"] or {}
            if content.get("entityId") == article_id:
                return content["entityUuid"]

        return None
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None
        
        return SCMPArticle._get_uuid(match.group(1))
    
    @classmethod
    @upstream_request_timer
    def get_data(cls, id):
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

        content = r.json()["data"]["content"]
        if content is None:
            raise ArticleNotFoundError(f"SCMP has no article for `{id}`")

        return content


if __name__ == "__main__":
    article = SCMPArticle.get_from_url(
        "https://www.scmp.com/news/china/military/article/3365081/mainland-chinas-ship-activity-near-taiwan-hits-record-third-month-row?module=top_story&pgtype=homepage"
    )

    print(article)
