from base64 import b64encode

import pytest

from providers.registry import *

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
    ),
    (
        TheAthleticArticle,
        "https://www.nytimes.com/athletic/7444334/2026/07/16/gianni-infantino-fifa-president-future/",
        "7444334"
    ),
    (
        NYTimesArticle,
        "https://www.nytimes.com/2026/07/25/opinion/boy-scouts-girls-gender.html",
        b64encode(b"/2026/07/25/opinion/boy-scouts-girls-gender.html").decode() # The Article ID is the path after https://www.nytimes.com
    ),
    (
        WashingtonPostArticle,
        "https://www.washingtonpost.com/opinions/2026/07/26/christopher-nolan-odyssey-shows-cost-online-rage/",
        b64encode(b"https://www.washingtonpost.com/opinions/2026/07/26/christopher-nolan-odyssey-shows-cost-online-rage/").decode() # The Article ID is the whole URL due to how Rainbow API is made
    ),
    (
        JDDArticle,
        "https://www.lejdd.fr/culture/expositions-la-france-au-fil-de-lart-179928",
        "179928"
    ),
    (
        FigaroArticle,
        "https://sante.lefigaro.fr/psychologie/complice-d-un-systeme-monstrueux-hans-asperger-le-psychiatre-qui-triait-les-enfants-pour-le-reich-20260728",
        b64encode(b"https://sante.lefigaro.fr/psychologie/complice-d-un-systeme-monstrueux-hans-asperger-le-psychiatre-qui-triait-les-enfants-pour-le-reich-20260728").decode() # The Article ID is the whole URL due to how Figaro's GraphQL is made
    ),
    (
        LiberationArticle,
        "https://www.liberation.fr/sports/football/zidane-nouveau-selectionneur-de-lequipe-de-france-une-oeuvre-de-patience-et-un-effet-retard-20260728_XJNJUDMOGNHT3MBMVYYJU374XE/",
        "XJNJUDMOGNHT3MBMVYYJU374XE"
    ),
    (
        EquipeArticle,
        "https://www.lequipe.fr/Football/Article/-il-montre-que-tout-le-monde-peut-reussir-dans-le-nord-de-marseille-la-castellane-est-fiere-de-zinedine-zidane-le-nouveau-selectionneur-des-bleus/1707695",
        "1707695"
    )
]


@pytest.mark.parametrize("cls,url,expected_id", ARTICLES)
def test_article_regex(cls, url, expected_id):
    assert cls.get_id_from_url(url) == expected_id

    for other in PROVIDERS:
        if other != cls:
            assert other.get_id_from_url(url) is None
