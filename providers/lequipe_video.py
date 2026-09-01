import re

import requests
from flask import abort
from bs4 import BeautifulSoup

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
    
    def _get_dm_token(channel):
        r = requests.get("https://iphdata.lequipe.fr/v6/php/dailymotion/getTokens.php")
        r.raise_for_status()
        data = r.json()
        
        for token in data["dm_tokens"]:
            if token["channel_name"] == channel:
                return token["token"]
        
        return None
    
    def _get_dailymotion_data(token):
        fields = [
            "aspect_ratio",
            "description",
            "duration",
            "id",
            "stream_hls_url",
            "thumbnail_url",
            "title",
            "mode"
        ]
        
        params = {
            "access_token": EquipeVideoArticle._get_dm_token("lequipe"),
            "fields": ",".join(fields)
        }
        
        r = requests.get("https://api.dailymotion.com/video/kVFLID8LndBks0J5wlo", params=params)
        r.raise_for_status()
        
        return r.json()

    def __init__(self, article_id: str):
        data = EquipeVideoArticle.get_data(article_id)
        
        metas = data["metas"]
        
        feature = EquipeVideoArticle._get_item(data["items"], "article_feature")
        body = EquipeVideoArticle._get_item(data["items"], "article_body")
        
        if feature is None or body is None:
            return abort(404)
        
        media = feature["media"]
        dm_data = EquipeVideoArticle._get_dailymotion_data(media["token"])
        
        hls_url = dm_data["stream_hls_url"]
        poster = dm_data["thumbnail_url"]
        aspect_ratio = dm_data["aspect_ratio"]
        
        # Video
        content = '<link href="https://cdn.jsdelivr.net/npm/video.js@8.23.8/dist/video-js.min.css" rel="stylesheet">'
        content += '<video style="aspect-ratio:'+str(aspect_ratio)+';" class="video-js" data-setup="{}" controls poster="'+poster+'"><source src="'+hls_url+'" type="application/x-mpegURL" /></video>'
        content += '<script src="https://cdn.jsdelivr.net/npm/video.js@8.23.8/dist/video.min.js"></script>'

        # Download links
        content += f"<p>Download <a href=\"{hls_url}\" target=\"_blank\">HLS</a> <a href=\"{poster}\" target=\"_blank\">Poster</a></p>"
        
        # Body
        for block in body["paragraphs"]:
            content += _build_block(block)

        super().__init__(
            id=article_id,
            headline=feature["title"],
            subheadline=metas["description"],
            content=content,
            url=metas["canonical"],
            image="",
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
