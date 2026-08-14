import re

import requests
from bs4 import BeautifulSoup
from flask import abort

from .common import Article, add_figure, fix_links, make_figcaption

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.lejdc\.fr\/.+_1(\d+)(?:\/?)"
)
# all id starts by "1" but isn't part of the id for some reason

def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    fix_links(soup)
    return soup.decode_contents()

def _build_content(content):
    typename = content["type"]
    
    if typename == "text":
        text = content["text"]
        for mark in content.get("marks", []):
            if mark["type"] == "link":
                attrs = mark["attrs"]
                link_attrs = f' href="{attrs["href"]}"'
                if attrs.get("rel"):
                    link_attrs += f' rel="{attrs["rel"]}"'
                if attrs.get("target"):
                    link_attrs += f' target="{attrs["target"]}"'
                text = f"<a{link_attrs}>{text}</a>"
        return _sanitize_html(text)
    
    if typename == "hardBreak":
        return "<br>"
    
    return ""

def _build_block(block):
    typename = block["type"]
    
    if typename == "paragraph":
        return "<p>" + "".join(_build_content(content) for content in block.get("content", [])) + "</p>"
    elif typename == "heading":
        level = block["attrs"]["level"]
        return f"<h{level}>" + "".join(_build_content(content) for content in block.get("content", [])) + f"</h{level}>"
    elif typename == "cf-paywall":
        return "".join(_build_block(subblock) for subblock in block.get("content", []))
    elif typename == "cf-image":
        attrs = block["attrs"]
        return add_figure(attrs["src"], attrs.get("caption", ""))
    elif typename == "cf-quote":
        return "<blockquote>" + "".join(_build_content(content) for content in block.get("content", [])) + "</blockquote>"
    elif typename == "cf-scribd":
        attrs = block["attrs"]
        return f'<iframe src="{attrs["url"]}" height="{attrs["height"]}" width="{attrs["width"]}">'
    elif typename == "bulletList":
        items = "".join(
            f"<li>{''.join(_build_block(subblock) for subblock in item.get('content', []))}</li>"
            for item in block.get("content", [])
        )
        return f"<ul>{items}</ul>"
    
    return ""


class JDCArticle(Article):
    SLUG = "jdc"
    PROVIDER = "Le Journal du Centre"
    FAVICON = "https://www.lejdc.fr/iv4/assets/favicon/favicon_JC/apple-touch-icon.png"

    def __init__(self, article_id: str):
        data = JDCArticle.get_data(article_id)
        
        article = data["data"]["article"]
        if article is None:
            return abort(404)
        
        image = article["mainPhoto"]["image"]["resize"]["url"]
        
        content = add_figure(image, make_figcaption(article["mainPhoto"]["caption"], article["mainPhoto"]["credit"]))
        
        if article["isTextToSpeechAvailable"] and article["textToSpeech"] is not None:
            content += f'<audio controls src="{article["textToSpeech"]["url"]}"></audio>'
        
        blocks = article["contentJson"]["content"]
        for block in blocks:
            content += _build_block(block)
            
        
        super().__init__(
            id=article["id"],
            headline=article["title"],
            subheadline=article["hat"],
            content=content,
            url="https://www.lejdc.fr"+article["url"],
            image=image
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None
        
        return match.group(1)
        
    def get_data(id):
        params = {
            "operationName": "articleDetail",
            "variables": '{"id":"'+id+'"}',
            "extensions": '{"persistedQuery":{"version":1,"sha256Hash":"fbc4a34e868e9079006dc3bbd132c501dbd2241849ab394e5d2408cacf0584ec"}}',
        }
        
        r = requests.get(
            "https://www.lejdc.fr/graphql",
            headers={"Content-Type": "application/json"},
            params=params
        )
        
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = JDCArticle.get_from_url(
        "https://www.lejdc.fr/nevers-58000/sports/pas-de-pluie-pas-de-natation-mais-un-beau-vainqueur-sur-le-triathlon-m-devenu-duathlon-m-de-nevers_15030790/"
    )

    print(article)