import base64
import re

import json
import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure

_URL_ID_PATTERN = re.compile(r"(https:\/\/.+\.lefigaro\.fr\/.+-\d{8})")


def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    
    for a in soup.find_all("a", href=True):
        a["target"] = "_blank"
        href = a["href"]
        
        id = FigaroArticle.get_id_from_url(href)
        if id is not None:
            a["href"] = f"/{FigaroArticle.SLUG}/{id}"
    
    return soup.decode_contents()


def _build_block(block):
    typename = block["__typename"]
    
    if typename == "Paragraph":
        return "<p>" + _sanitize_html(block["text"]) + "</p>"
    elif typename == "Heading":
        return f"<h2>{block['text']}</h2>"
    elif typename == "Photo":
        return add_figure(block['image']['url'], f"{block['caption']} -- {block['credit']}", f"{block['caption']} -- {block['credit']}")
    elif typename == "Quote":
        return f"<blockquote>{block['text']}<br><br>- {block['credit']}</blockquote>"
    elif typename == "ParagraphWithPaywall":
        return "<p>" + _sanitize_html(block["paywall"]["text"]) + "</p>"
    
    return ""

class FigaroArticle(Article):
    SLUG = "lf"
    PROVIDER = "Le Figaro"
    
    def __init__(self, article_id: str):
        article_path = base64.b64decode(article_id).decode()
        
        
        variables = json.dumps({
            "url": article_path
        })
        r = requests.get(
            f"https://api-graphql.lefigaro.fr/graphql", params={"id": "FigaroCoreMobile_resourceByUrl_persistent_47eb9ddbda1ea9c3194af6af47800cd54a0475a6df1da0d8e5ef1770c2c240cc", "variables": variables}
        )
        
        r.raise_for_status()
        data = r.json()["data"]["resource"]

        content = f"<audio controls src=\"{data['audio']['url']}\"></audio>"
        for block in data["body"]["structured"]:
            content += _build_block(block)

        content = add_figure(
            data["mainMedia"]["image"]["url"],
            f"{data['mainMedia']['caption']} -- {data['mainMedia']['credit']}"
        ) + content

        super().__init__(
            id=article_id,
            headline=data["headline"],
            subheadline=data["standfirst"],
            content=content,
            url=data["url"],
            image=data["mainMedia"]["image"]["url"]
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return base64.b64encode(match.group(1).encode()).decode("ascii")


if __name__ == "__main__":
    article = FigaroArticle.get_from_url("https://sante.lefigaro.fr/psychologie/complice-d-un-systeme-monstrueux-hans-asperger-le-psychiatre-qui-triait-les-enfants-pour-le-reich-20260728")

    print(article)
