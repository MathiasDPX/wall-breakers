from datetime import datetime
import base64
import json
import re
from random import choice

import requests
from bs4 import BeautifulSoup

from .exceptions import ArticleNotFoundError, sentry_block_error
from .common import Article, add_figure, decode_id, fix_link, fix_links, make_figcaption
from metrics import upstream_request_timer

_URL_ID_PATTERN = re.compile(r"(https:\/\/.+\.lefigaro\.fr\/.+-\d{8})")


def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    fix_links(soup)
    
    return soup.decode_contents()


def _thumbnail_figcaption(block):
    thumbnail = block.get("thumbnail") or {}

    return make_figcaption(thumbnail.get("caption"), thumbnail.get("credit"))

def _thumbnail_url(block):
    return ((block.get("thumbnail") or {}).get("image") or {}).get("url")

def _build_video(block):
    videos = FigaroArticle.get_videos(block["id"])
    mp4s = [video for video in videos if video.get("type") == "MP4"]

    if not mp4s:
        thumbnail = _thumbnail_url(block)
        return add_figure(thumbnail, _thumbnail_figcaption(block)) if thumbnail else ""

    return add_figure(choice(mp4s).get("url", ""), _thumbnail_figcaption(block))

def _build_brightcove(block):
    # Brightcove no longer serves the raw streams, so embed the player instead
    player = f"https://players.brightcove.net/{block['accountId']}/{block['playerId']}_default/index.html?videoId={block['id']}"
    caption = _thumbnail_figcaption(block)
    caption = f"<figcaption>{caption}</figcaption>" if caption else ""

    return f'<figure><iframe src="{player}" allowfullscreen loading="lazy"></iframe>{caption}</figure>'

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
    elif typename == "VideoFigaro":
        return _build_video(block)
    elif typename == "Link":
        prefix = block.get("prefix", "").lower()
        if "lire aussi" in prefix or "voir aussi" in prefix:
            return ""
    elif typename == "File":
        return f'<a target="_blank" href="{block["url"]}">{block["title"]}</a>'
    elif typename in ["Tweet", "Instagram"]:
        return (block.get("sourceCode") or "") + (block.get("script") or "")
    elif typename == "Brightcove":
        return _build_brightcove(block)
    elif typename == "Frame":
        return f"<aside><h3>{block['title']}</h3><p>{_sanitize_html(block['text'])}</p></aside>"
    elif typename == "CTALink":
        link = block["link"]
        return f'<p><a target="_blank" href="{fix_link(link["url"])}">{link["title"]}</a></p>'
    elif typename == "HorizontalRule":
        return "<hr>"
    elif typename == "FreeHtml":
        return _sanitize_html(block.get("sourceCode", ""))
    elif typename == "List":
        tag = "ol" if block.get("listType") == "ORDERED" else "ul"
        items = "".join(f"<li>{_sanitize_html(item)}</li>" for item in block.get("list", []))
        return f"<{tag}>{items}</{tag}>"
    elif typename == "Table":
        return f"<table>{_sanitize_html(block.get('text', ''))}</table>"
    elif typename == "VideoIframe":
        return f'<figure><iframe src="{block["src"]}" allowfullscreen frameborder="0" loading="lazy"></iframe></figure>'
    
    sentry_block_error(typename)
    
    return ""

class FigaroArticle(Article):
    SLUG = "lf"
    PROVIDER = "Le Figaro"
    FAVICON = "https://www.lefigaro.fr/apple-touch-icon.png"
    
    def __init__(self, article_id: str):
        data = FigaroArticle.get_data(article_id)

        if data is None:
            raise ArticleNotFoundError(f"Le Figaro has no article for `{article_id}`")

        content = ""
        thumbnail = "static/images/thumbnail.jpg"

        main_media = data.get("mainMedia")
        if main_media:
            mainMediaType = main_media["__typename"]
            if mainMediaType == "Photo":
                content = add_figure(
                    main_media["image"]["url"],
                    make_figcaption(main_media['caption'], main_media['credit'])
                )
                thumbnail = main_media["image"]["url"]
            elif mainMediaType == "VideoFigaro":
                content = _build_video(main_media)
                thumbnail = _thumbnail_url(main_media) or thumbnail
            elif mainMediaType == "Brightcove":
                content = _build_brightcove(main_media)
                thumbnail = _thumbnail_url(main_media) or thumbnail

        video_main_media = data.get("videoMainMedia")
        if video_main_media:
            content = _build_video(video_main_media)
            thumbnail = _thumbnail_url(video_main_media) or thumbnail
        
        audio = data.get("audio")
        if audio and "url" in audio:
            content += f"<audio controls src=\"{audio['url']}\"></audio>"

        
        for block in data.get("body", {}).get("structured", []):
            content += _build_block(block)

        published_at = data.get("publishedAt")
            
        super().__init__(
            id=article_id,
            headline=data["headline"],
            subheadline=data.get("standfirst", ""),
            content=content,
            url=data["url"],
            image=thumbnail,
            publication_date=datetime.fromisoformat(published_at) if published_at else None
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return base64.b64encode(match.group(1).encode()).decode("ascii")
    
    @classmethod
    @upstream_request_timer
    def get_data(cls, id):
        article_path = decode_id(id)
        
        variables = json.dumps({
            "url": article_path
        })
        r = requests.get(
            "https://api-graphql.lefigaro.fr/graphql", params={"id": "FigaroCoreMobile_resourceByUrl_persistent_47eb9ddbda1ea9c3194af6af47800cd54a0475a6df1da0d8e5ef1770c2c240cc", "variables": variables}
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
