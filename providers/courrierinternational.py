import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

from .common import Article, fix_links

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.courrierinternational\.com\/[a-z\/-]+_(\d+).*"
)

_URI_ID_PATTERN = re.compile(
    r"crifr:\/\/article\?id=(\d+).*"
)


def fix_cri_uri(uri: str):
    if not uri.startswith("crifr://"):
        return uri
        
    if uri.startswith("crifr://open-url"):
        parameters = uri.split("&")
        for parameter in parameters:
            if parameter.startswith("url="):
                return unquote(parameter[4:])
    
    return uri


class CourrierInternationalArticle(Article):
    SLUG = "ci"
    PROVIDER = "Courrier International"
    FAVICON = "https://www.courrierinternational.com/bucket/assets/64d83f984faf88a94dd821bcc4640b47bfab388b/img/logos/favicon.svg"
    
    def __init__(self, article_id: str):
        data = CourrierInternationalArticle.get_data(article_id)

        soup = BeautifulSoup(data["templates"]["raw_content"]["content"], features="html.parser")
        if soup.find_all("div", attrs={"class": "article_content"}):
            soup = soup.find("div", attrs={"class": "article_content"})

        illustration = soup.select_one("header.article-header figure img")
        image = illustration.get("src") if illustration else None

        for container in soup.select("h1.article-title, ul.article-breadcrumbs, p.article-lede, a.article-source, div.wrap span.read-more-label, header.article-header, div.asset-read-more, div.article-secondary, div.favorites-reserved"):
            container.decompose()

        # Obliterate document metadata and non-content elements
        for tag in soup.select("head, script, style, aside"):
            if tag.parent is not None:
                tag.decompose()

        for tag in soup.find_all():
            # Keep only allowed tags
            if tag.name not in ("figure", "figcaption", "p", "em", "a", "img", "h1", "h2", "h3", "h4", "h5", "h6", "b", "ul", "li"):
                tag.unwrap()

            # Keep only allowed attributes
            tag.attrs = {
                key: value
                for key, value in tag.attrs.items()
                if key in ("href", "src", "srcset", "fetchpriority", "alt", "aria-label",)
            }

        # Remove empty tags
        for tag in soup.find_all():
            if (
                not tag.get_text(strip=True)
                and not tag.find()
                and tag.name not in ["img", "br", "hr", "input"]
            ):
                tag.decompose()


        for a in soup.find_all("a", href=True):
            a["href"] = fix_cri_uri(a["href"])
        
        fix_links(soup)

        figure = soup.find("figure")
        if figure:
            if data["audio"]["enabled"]:
                audio = soup.new_tag("audio", controls=True)
                audio["src"] = data["audio"]["audio_track"]["media_url"]
                figure.insert_after(audio)

            img = figure.find("img")
            if img and image is None:
                image = img.get("src")
        else:
            if data["audio"]["enabled"]:
                audio = soup.new_tag("audio", controls=True)
                audio["src"] = data["audio"]["audio_track"]["media_url"]
                soup.insert(0, audio)

        content = soup.decode_contents()
        content = content.replace("{{{ scripts_bottom }}}", "")

        super().__init__(
            id=article_id,
            headline=data["element"]["title"],
            subheadline=data["element"]["subtitle"],
            content=content,
            url=data["sharing"]["configurations"]["default"]["url"],
            image=image
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is not None:
            return match.group(1)
        
        match = _URI_ID_PATTERN.search(url)
        if match is not None:
            return match.group(1)
        
        return None
    
    def get_data(id):
        r = requests.get(
            f"https://apps.courrierinternational.com/cri/v1/premium-android-tablet/article?id={id}"
        )
        r.raise_for_status()
        return r.json()
    
    def get_readable_data(id):
        data = CourrierInternationalArticle.get_data(id)
        return data["templates"]["raw_content"]["content"]


if __name__ == "__main__":
    article = CourrierInternationalArticle.get_from_url("https://www.courrierinternational.com/article/vu-de-belgique-en-pleine-urgence-climatique-le-soutien-des-verts-dispute-avant-la-presidentielle-francaise_263808")

    print(article)
