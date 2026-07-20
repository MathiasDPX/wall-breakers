from providers import *
import pytest

ARTICLES = [
    (
        LeParisienArticle,
        "https://www.leparisien.fr/sports/football/coupe-du-monde/france-angleterre-la-composition-probable-des-bleus-avec-zaire-emery-cherki-olise-et-mbappe-18-07-2026-ZMLNSNIHBVGEPALOLJ3KGMBQAI.php",
        "ZMLNSNIHBVGEPALOLJ3KGMBQAI",
    ),
    (
        LeMondeArticle,
        "https://www.lemonde.fr/planete/article/2026/07/18/au-canada-les-feux-a-repetition-bouleversent-la-foret-boreale_6724998_3244.html",
        "6724998",
    ),
    (
        LeTelegrammeArticle,
        "https://www.letelegramme.fr/finistere/landerneau-29800/a-landerneau-une-journee-pour-celebrer-la-culture-bretonne-le-25-juillet-avec-fest-e-landerne-7086034.php",
        "7086034",
    ),
    (
        LesEchosArticle,
        "https://www.lesechos.fr/monde/etats-unis/lespagne-gagne-la-coupe-du-monde-de-foot-et-la-fifa-empoche-un-pactole-2243070",
        "2243070"
    )
]


PROVIDERS = [
    LeParisienArticle,
    LeMondeArticle,
    LeTelegrammeArticle,
]


@pytest.mark.parametrize("cls,url,expected_id", ARTICLES)
def test_article_regex(cls, url, expected_id):
    assert cls.get_id_from_url(url) == expected_id

    for other in PROVIDERS:
        if other != cls:
            assert other.get_id_from_url(url) is None