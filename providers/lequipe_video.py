import re

import requests
from flask import abort
from bs4 import BeautifulSoup

from .exceptions import sentry_block_error
from .common import Article, fix_link, fix_links, add_figure

_URL_ID_PATTERN = re.compile(r"https:\/\/www\.lequipe\.fr\/explore\/video\/.+\/(\d+)")

def _build_block(block):
    typename = block["__type"]

    if typename == "article_paragraph":
        if block["layout"] != "text" and block["layout"] != "chapo":
            return ""

        return "<p>" + _sanitize_html(block.get("content", "")) + "</p>"
    elif typename == "article_paragraph_media":
        return add_figure(
            _build_media(block["media"], 1000), block["media"].get("legende")
        )
        
    sentry_block_error(typename)

    return ""

def _build_media(media, height):
    image = media["url"].replace("{width}", str(int(height * media["ratio"])))
    image = image.replace("{height}", str(height))
    image = image.replace("{quality}", "80")

    return image

def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")

    fix_links(soup)
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("/"):
            a["href"] = fix_link(f"https://www.lequipe.fr{a['href']}")

    return soup.decode_contents()

class EquipeVideoArticle(Article):
    SLUG = "ekipv"
    PROVIDER = "L'Équipe Vidéo"
    FAVICON = "https://www.lequipe.fr/favicons/favicon.svg"

    def _get_item(items, layout):
        for item in items:
            if item["layout"] == layout:
                return item["objet"]

        return None
    
    def _get_dm_video_id(media):
        return media.get("dm_id") or media.get("id")

    def __init__(self, article_id: str):
        data = EquipeVideoArticle.get_data(article_id)
        
        metas = data["metas"]
        
        feature = EquipeVideoArticle._get_item(data["items"], "article_feature")
        body = EquipeVideoArticle._get_item(data["items"], "article_body")
        
        if feature is None or body is None:
            return abort(404)
        
        media = feature["media"]
        dm_video_id = EquipeVideoArticle._get_dm_video_id(media)

        content = f'<div class="video-wrapper"><iframe allowfullscreen frameborder="0" width="100%" src="//www.dailymotion.com/embed/video/{dm_video_id}"></iframe></div>'
        
        # Download links
        content += f"<p><a href=\"https://www.dailymotion.com/video/{dm_video_id}\" target=\"_blank\">Dailymotion</a></p>"
        
        # Body
        for block in body["paragraphs"]:
            content += _build_block(block)
            
        sharing_image = _build_media(data["metas"]["sharing_image"], 1000)

        super().__init__(
            id=article_id,
            headline=feature["title"],
            subheadline=metas["description"],
            content=content,
            url=metas["canonical"],
            image=sharing_image,
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)
    
    def get_data(id):
        r = requests.get(f"https://dwh.lequipe.fr/api/video/media/{id}?version=2.1&platform=android")

        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = EquipeVideoArticle.get_from_url("https://www.lequipe.fr/explore/video/l-equipe-explore-documentaire-blandine-l-hirondel-une-espece-rare/20239956")

    print(article)
