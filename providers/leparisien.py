from .common import Article
import re
import requests


_URL_ID_PATTERN = re.compile(
    r".+-\d{2}-\d{2}-\d{4}-([A-Z0-9]{26})\.php"
)



class LeParisienArticle(Article):

    def __init__(self, article_id: str):
        r = requests.get(
            f"https://gateway-api.leparisien.fr/v1/contents/articles/{article_id}"
        )
        r.raise_for_status()
        data = r.json()["story"]

        super().__init__(
            id="leparisien:"+data["_id"],
            headline=data["headlines"]["basic"],
            subheadline=data["subheadlines"]["basic"],
            content=data["bodyContent"],
            image=data["promo_items"]["basic"]["resize_url"]
        )

    @classmethod
    def get_from_url(cls, url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return cls(match.group(1))


if __name__ == "__main__":
    article = LeParisienArticle.get_from_url(
        "https://www.leparisien.fr/sports/football/coupe-du-monde/france-angleterre-la-composition-probable-des-bleus-avec-zaire-emery-cherki-olise-et-mbappe-18-07-2026-ZMLNSNIHBVGEPALOLJ3KGMBQAI.php"
    )

    print(article)