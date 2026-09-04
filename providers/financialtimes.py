import re

import requests
from bs4 import BeautifulSoup

from .exceptions import sentry_block_error
from .common import Article, fix_links, add_figure, make_figcaption

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.ft\.com\/content\/([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}).*"
)

def _build_block(block, references):
    # All subblocks are build with unsafe set to True cuz the body blocks will be builds safely
    typename = block["type"]
    
    if typename == "text":
        return block["value"]
    elif typename == "break":
        return "<br>"
    elif typename == "link":
        content = _build_blocks(block["children"], unsafe=True, references=references)
        return f"<a href=\"{block['url']}\" title=\"{block['title']}\">{content}</a>"
    elif typename == "paragraph":
        return "<p>" + _build_blocks(block["children"], unsafe=True, references=references) + "</p>"
    elif typename == "image-set":
        ref = references[block["data"]["referenceIndex"]]
        picture = ref["picture"]
        image = picture["images"][0]
        url = image["sourceSet"][len(image["sourceSet"]) // 2]["url"]
        return add_figure(url, make_figcaption(picture["caption"], picture["credit"]))
    elif typename == "video":
        ref = references[block["data"]["referenceIndex"]]
        
        r = requests.get("https://next-media-api.ft.com/v1/" + ref["id"])
        r.raise_for_status()
        return _add_video(r.json())
    
    sentry_block_error(typename)
    
    return ""

def _build_blocks(blocks, references, unsafe=False):
    content = ""
    for block in blocks:
        content += _build_block(block, references)
        
    if unsafe is False:
        soup = BeautifulSoup(content, features="html.parser")
        fix_links(soup)
        content = soup.decode_contents()
        
    return content


def _add_video(data):
    max_quality = None
    for quality in data["renditions"]:
        if max_quality is None:
            max_quality = quality
            continue
        
        if quality["pixelWidth"] * quality["pixelHeight"] < max_quality["pixelWidth"] * max_quality["pixelHeight"]:
            continue
        
        max_quality = quality
    
    if max_quality is None:
        return ""
    
    posterUrl = data.get("mainImageUrl")
    title = data.get("title")
    captionsUrl = data.get("captionsUrl")
    
    poster_tag = ""
    if posterUrl is not None:
        poster_tag = f" poster=\"{posterUrl}\""
    
    captions_tag = ""
    if captionsUrl is not None:
        captions_tag = f" <track kind=\"captions\" src=\"{captionsUrl}\" />"
        
    title_tag = ""
    if title is not None:
        title_tag = f" title=\"{title}\""
        
    return f"<video controls><source src=\"{max_quality['url']}\"{poster_tag}{title_tag}>{captions_tag}</video>"

class FinancialTimesArticle(Article):
    SLUG = "ft"
    PROVIDER = "Financial Times"
    FAVICON = "https://images.ft.com/v3/image/raw/ftlogo-v1%3Abrand-ft-logo-square-coloured?source=page-kit&format=svg"

    def __init__(self, article_id: str):
        data = FinancialTimesArticle.get_data(article_id)
        
        image = "static/images/thumbnail.jpg"
        if "mainImage" in data:
            image = data["mainImage"]
            
        body = data["body"]["structured"]["tree"]
        content = add_figure(image["url"], make_figcaption(image["caption"], image["credit"]))
        content += _build_blocks(body["children"], data["body"]["structured"]["references"])

        super().__init__(
            id=article_id,
            headline=data["title"],
            subheadline=data["standfirst"],
            content=content,
            url=data["url"],
            image=image["url"],
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)
    
    def get_data(id):
        headers = {
            "Host": "app-api.ft.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; OXF-AN10 Build/UQ1A.240205.07131809; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/124.0.6367.82 Mobile Safari/537.36 ft-app-android/2.297.0-snapshot.86.13390707531003.9209+5a63db4 fruitcake/2142297000 2.297.0-snapshot.86.13390707531003.9209+5a63db4 (640/640dpi ; 1440x2560 ; Build/UQ1A.240205.07131809 ; handset ; model: OXF-AN10 Build/UQ1A.240205.07131809 ; AndroidVersion: Android 14 ; manufacturer: Honor) sencha"
        }
        
        r = requests.get(
            f"https://app-api.ft.com/__content/v6/article/{id}?useVanities=false",
            headers=headers
        )
        r.raise_for_status()
        return r.json()["data"]["content"]


if __name__ == "__main__":
    article = FinancialTimesArticle.get_from_url("https://www.ft.com/content/32a70a3c-7d28-40b4-808e-36edb58c7d01")
    
    print(article)
