from random import choice
import base64
import re

import json
import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure, fix_links, make_figcaption

_URL_ID_PATTERN = re.compile(r"(https:\/\/.+\.lefigaro\.fr\/.+-\d{8})")


def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    fix_links(soup)
    
    return soup.decode_contents()


def _build_block(block):
    typename = block["__typename"]
    
    if typename == "Paragraph":
        return "<p>" + _sanitize_html(block["text"]) + "</p>"
    elif typename == "Heading":
        return f"<h2>{block['text']}</h2>"
    elif typename == "Photo":
        return add_figure(block['image']['url'], f"{block['caption']} &copy; {block['credit']}")
    elif typename == "Quote":
        return f"<blockquote>{block['text']}<br><br>- {block['credit']}</blockquote>"
    elif typename == "ParagraphWithPaywall":
        return "<p>" + _sanitize_html(block["paywall"]["text"]) + "</p>"
    
    return ""

class FigaroArticle(Article):
    SLUG = "lf"
    PROVIDER = "Le Figaro"
    
    def __init__(self, article_id: str):
        data = FigaroArticle.get_data(article_id)

        mainMediaType = data["mainMedia"]["__typename"]
        thumbnail = "static/images/thumbnail.jpg"
        if mainMediaType == "Photo":
            content = add_figure(
                data["mainMedia"]["image"]["url"],
                make_figcaption(data['mainMedia']['caption'], data['mainMedia']['credit'])
            )
            thumbnail = data["mainMedia"]["image"]["url"]
        elif mainMediaType == "VideoFigaro":
            videos = FigaroArticle.get_videos(data["mainMedia"]["id"])
            mp4s = [video for video in videos if video.get("type") == "MP4"]
            
            content = add_figure(
                choice(mp4s).get("url", ""),
                make_figcaption(data['mainMedia']['thumbnail']['caption'], data['mainMedia']['thumbnail']['credit'])
            )
            thumbnail = data["mainMedia"]["thumbnail"]["image"]["url"]
        
        if data["audio"] != None:
            if "url" in data['audio']:
                content += f"<audio controls src=\"{data['audio']['url']}\"></audio>"

        
        for block in data["body"]["structured"]:
            content += _build_block(block)
            
        super().__init__(
            id=article_id,
            headline=data["headline"],
            subheadline=data["standfirst"],
            content=content,
            url=data["url"],
            image=thumbnail
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return base64.b64encode(match.group(1).encode()).decode("ascii")
    
    def get_data(id):
        article_path = base64.b64decode(id).decode()
        
        variables = json.dumps({
            "url": article_path
        })
        r = requests.get(
            f"https://api-graphql.lefigaro.fr/graphql", params={"id": "FigaroCoreMobile_resourceByUrl_persistent_47eb9ddbda1ea9c3194af6af47800cd54a0475a6df1da0d8e5ef1770c2c240cc", "variables": variables}
        )
        
        r.raise_for_status()
        return r.json()["data"]["resource"]

    def get_videos(video_id):
        variables = json.dumps({
            "videoFigaroId": video_id
        })
        
        r = requests.get("https://api-graphql.lefigaro.fr/graphql", params={"id": "FigaroCoreMobile_videoFigaroAssets_persistent_1a65935f94d8bb8968d84332ecec012542855262532dcc3436f73ec639669368", "variables": variables})
        r.raise_for_status()
        
        return r.json()["data"]["videoFigaroAssets"]


if __name__ == "__main__":
    article = FigaroArticle.get_from_url("https://sante.lefigaro.fr/psychologie/complice-d-un-systeme-monstrueux-hans-asperger-le-psychiatre-qui-triait-les-enfants-pour-le-reich-20260728")

    print(article)
