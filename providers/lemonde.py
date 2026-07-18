from .common import Article
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

        super().__init__(
            id="lemonde:"+article,
            headline=data["template_vars"]["basic"],
            subheadline=data["template_vars"]["share_kicker"],
            content=data["template_vars"]["content"],
            image=None, # TODO: get from og_metas
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