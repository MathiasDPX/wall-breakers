from .common import Article
from bs4 import BeautifulSoup
from urllib.parse import unquote
import re
import requests


_URL_ID_PATTERN = re.compile(
    r".+_(\d+)_.+\.html"
)


class LeMondeArticle(Article):
    def __init__(self, article_id: str):
        r = requests.get(
            f"https://apps.lemonde.fr/aec/v1/premium-ios-tablet/article/{article_id}"
        )
        r.raise_for_status()
        data = r.json()

        soup = BeautifulSoup(data["template_vars"]["content"], features="html.parser").find_all(
            "div", attrs={"class": "article_content"})[0]

        # Remove See Also, Inread and PubStack containers
        for container in soup.select("div.see-also-container, div.inread-container, div.pubstack-container"):
            container.decompose()

        for tag in soup.find_all():
            # Remove unwanted attributes
            tag.attrs.pop('style', None)
            tag.attrs.pop('data-read-progression', None)
            tag.attrs.pop('id', None)
            tag.attrs.pop('class', None)
            tag.attrs.pop('onload', None)
            tag.attrs.pop('onerror', None)
            tag.attrs.pop('"', None)

            # Remove empty tags
            if not tag.get_text(strip=True) and not tag.find() and tag.name not in ["img", "br", "hr", "input"]:
                tag.decompose()

        for img in soup.find_all("a", href=True):
            url = img["href"].replace("lmfr://illustration?url=", "")
            img["href"] = unquote(url)

        for a in soup.find_all("a", role="button"):
            a.unwrap()

        for div in soup.select("figure > div"):
            div.unwrap()

        content = soup.decode_contents()

        super().__init__(
            id="lemonde:"+article_id,
            headline=data["template_vars"]["seo_title"],
            subheadline=data["template_vars"]["share_kicker"],
            content=content,
            image=None,
        )

    @classmethod
    def get_from_url(cls, url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return cls(match.group(1))


if __name__ == "__main__":
    article = LeMondeArticle.get_from_url(
        "https://www.lemonde.fr/international/article/2026/07/17/pourquoi-la-guerre-hybride-menee-par-la-russie-pousse-la-france-a-hausser-le-ton_6724233_3210.html"
    )

    print(article)
