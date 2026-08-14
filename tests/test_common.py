from base64 import b64encode

import pytest
import requests

from providers.common import get_article_from_url
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
    ),
    (
        OuestFranceArticle,
        "https://www.ouest-france.fr/societe/ruralites/tu-es-un-peu-le-maire-sans-lecharpe-les-secretaires-de-mairie-espece-en-voie-de-disparition-1b28e6b2-66d4-11f0-bb8e-c5b2af864a8a",
        "1b28e6b2-66d4-11f0-bb8e-c5b2af864a8a"
    ),
    (
        CourrierInternationalArticle,
        "https://www.courrierinternational.com/article/sciences-les-animaux-revent-ils-aussi_198382_1",
        "198382"
    ),
    (
        MediapartArticle,
        "https://www.mediapart.fr/journal/international/020826/les-jours-comptes-de-gianni-infantino-la-tete-du-football-mondial",
        b64encode(b"https://www.mediapart.fr/journal/international/020826/les-jours-comptes-de-gianni-infantino-la-tete-du-football-mondial").decode()
    ),
    (
        ActuArticle,
        "https://actu.fr/monde/deux-morts-et-18-000-cas-ce-que-l-on-sait-de-cette-epidemie-de-diarrhees-explosives-qui-sevit-aux-etats-unis_64626347.html",
        "64626347"
    ),
    (
        CharenteLibreArticle,
        "https://www.charentelibre.fr/charente/champagne-mouton/cette-annee-on-va-s-interesser-au-theme-du-jardin-le-7e-festival-du-film-franco-britannique-de-champagne-mouton-cultive-son-originalite-30126109.php",
        "30126109"
    ),
    (
        ExpressArticle,
        "https://www.lexpress.fr/monde/proche-moyen-orient/leurope-a-besoin-du-maroc-pour-controler-sa-frontiere-sud-lanalyse-de-nando-sigona-ZR2OSRZ5Q5F3ZCKA6MBBI3WZOY/",
        "ZR2OSRZ5Q5F3ZCKA6MBBI3WZOY"
    ),
    (
        ParisMatchArticle,
        "https://www.parismatch.com/actu/politique/claude-chirac-on-a-tout-fait-des-cafes-aux-photocopies-273699",
        "273699"
    ),
    (
        NouvelObsArticle,
        "https://www.nouvelobs.com/monde/20260807.OBS117259/sur-les-traces-d-ulysse-de-troie-a-djerba-nous-reprenons-la-mer-l-ame-navree.html",
        "20260807.OBS117259"
    ),
    (
        TeleramaArticle,
        "https://www.telerama.fr/series-tv/alley-cats-sur-netflix-ricky-gervais-aux-manettes-d-une-serie-animee-feline-et-chat-nous-plait-bien_cri-7045364.php",
        b64encode(b"/series-tv/alley-cats-sur-netflix-ricky-gervais-aux-manettes-d-une-serie-animee-feline-et-chat-nous-plait-bien_cri-7045364.php").decode()
    ),
    (
        JDCArticle,
        "https://www.lejdc.fr/nevers-58000/sports/triathlon-de-nevers-vingtieme-de-la-course-alice-chevasson-finit-premiere-feminine-du-duathlon-m_15030796/",
        "5030796"
    ),
    (
        FinancialTimesArticle,
        "https://www.ft.com/content/63a28eea-9d73-487b-bb46-34530e215fce?syn-25a6b1a6=1",
        "63a28eea-9d73-487b-bb46-34530e215fce"
    ),
    (
        NikkeiAsiaArticle,
        "https://asia.nikkei.com/spotlight/policy-asia/can-takaichi-s-2.3tn-bet-on-industrial-policy-revive-growth-in-japan",
        b64encode(b"/spotlight/policy-asia/can-takaichi-s-2.3tn-bet-on-industrial-policy-revive-growth-in-japan").decode()
    )
]


@pytest.mark.parametrize("cls,url,expected_id", ARTICLES)
def test_article_regex(cls, url, expected_id):
    assert cls.get_id_from_url(url) == expected_id

    for other in PROVIDERS:
        if other != cls:
            assert other.get_id_from_url(url) is None


@pytest.mark.parametrize("cls,url,expected_id", ARTICLES)
def test_get_article_from_url(cls, url, expected_id):
    assert get_article_from_url(url) == (cls, expected_id)

@pytest.mark.parametrize("cls,url,expected_id", ARTICLES)
def test_favicon(cls, url, expected_id):
    if getattr(cls, "FAVICON", None):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:153.0) Gecko/20100101 Firefox/153.0"
        }
        r = requests.get(cls.FAVICON, headers=headers)
        assert r.status_code == 200
        
    assert True