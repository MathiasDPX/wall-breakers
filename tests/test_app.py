import os

import pytest
from dotenv import load_dotenv

from main import app
from providers.registry import *

load_dotenv()

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

OUESTFRANCE_ENABLED = os.getenv("OUESTFRANCE_REFRESH_TOKEN", None) != None
MEDIAPART_ENABLED = os.getenv("PIERREVIVES_USERNAME") is not None and os.getenv("PIERREVIVES_PASSWORD") is not None

URLS = [
    "https://www.leparisien.fr/sports/football/coupe-du-monde/france-angleterre-la-composition-probable-des-bleus-avec-zaire-emery-cherki-olise-et-mbappe-18-07-2026-ZMLNSNIHBVGEPALOLJ3KGMBQAI.php",
    "https://www.lemonde.fr/planete/article/2026/07/18/au-canada-les-feux-a-repetition-bouleversent-la-foret-boreale_6724998_3244.html",
    "https://www.letelegramme.fr/finistere/landerneau-29800/a-landerneau-une-journee-pour-celebrer-la-culture-bretonne-le-25-juillet-avec-fest-e-landerne-7086034.php",
    "https://www.lesechos.fr/monde/etats-unis/lespagne-gagne-la-coupe-du-monde-de-foot-et-la-fifa-empoche-un-pactole-2243070",
    "https://www.nytimes.com/athletic/7444334/2026/07/16/gianni-infantino-fifa-president-future/",
    #"https://www.nytimes.com/2026/07/25/opinion/boy-scouts-girls-gender.html", Disabled as it's not working due to Datadome anti-scraping protection
    "https://www.washingtonpost.com/opinions/2026/07/26/christopher-nolan-odyssey-shows-cost-online-rage/",
    "https://www.lejdd.fr/culture/expositions-la-france-au-fil-de-lart-179928",
    "https://sante.lefigaro.fr/psychologie/complice-d-un-systeme-monstrueux-hans-asperger-le-psychiatre-qui-triait-les-enfants-pour-le-reich-20260728",
    "https://www.liberation.fr/sports/football/zidane-nouveau-selectionneur-de-lequipe-de-france-une-oeuvre-de-patience-et-un-effet-retard-20260728_XJNJUDMOGNHT3MBMVYYJU374XE/",
    "https://www.lequipe.fr/Football/Article/-il-montre-que-tout-le-monde-peut-reussir-dans-le-nord-de-marseille-la-castellane-est-fiere-de-zinedine-zidane-le-nouveau-selectionneur-des-bleus/1707695",
    "https://www.ouest-france.fr/societe/ruralites/tu-es-un-peu-le-maire-sans-lecharpe-les-secretaires-de-mairie-espece-en-voie-de-disparition-1b28e6b2-66d4-11f0-bb8e-c5b2af864a8a",
    "https://www.courrierinternational.com/article/sciences-les-animaux-revent-ils-aussi_198382_1",
    "https://www.mediapart.fr/journal/international/020826/les-jours-comptes-de-gianni-infantino-la-tete-du-football-mondial",
    "https://actu.fr/monde/deux-morts-et-18-000-cas-ce-que-l-on-sait-de-cette-epidemie-de-diarrhees-explosives-qui-sevit-aux-etats-unis_64626347.html",
    "https://www.charentelibre.fr/charente/champagne-mouton/cette-annee-on-va-s-interesser-au-theme-du-jardin-le-7e-festival-du-film-franco-britannique-de-champagne-mouton-cultive-son-originalite-30126109.php",
    "https://www.lexpress.fr/monde/proche-moyen-orient/leurope-a-besoin-du-maroc-pour-controler-sa-frontiere-sud-lanalyse-de-nando-sigona-ZR2OSRZ5Q5F3ZCKA6MBBI3WZOY/",
    "https://www.parismatch.com/actu/politique/claude-chirac-on-a-tout-fait-des-cafes-aux-photocopies-273699",
    "https://www.nouvelobs.com/monde/20260807.OBS117259/sur-les-traces-d-ulysse-de-troie-a-djerba-nous-reprenons-la-mer-l-ame-navree.html",
    "https://www.telerama.fr/series-tv/alley-cats-sur-netflix-ricky-gervais-aux-manettes-d-une-serie-animee-feline-et-chat-nous-plait-bien_cri-7045364.php",
    "https://www.lejdc.fr/nevers-58000/sports/triathlon-de-nevers-vingtieme-de-la-course-alice-chevasson-finit-premiere-feminine-du-duathlon-m_15030796/",
    "https://www.ft.com/content/63a28eea-9d73-487b-bb46-34530e215fce",
    "https://asia.nikkei.com/spotlight/policy-asia/can-takaichi-s-2.3tn-bet-on-industrial-policy-revive-growth-in-japan",
    "https://www.scmp.com/news/china/military/article/3365081/mainland-chinas-ship-activity-near-taiwan-hits-record-third-month-row?module=top_story&pgtype=homepage",
    "https://www.lejsl.com/economie/2026/08/24/un-duo-mere-fille-ouvre-une-boutique-de-seconde-main-pour-enfants",
    "https://www.dna.fr/faits-divers-justice/2022/12/16/la-charte-des-dna",
    "https://www.estrepublicain.fr/societe/2021/01/31/les-grandes-histoires-de-l-est-le-podcast-des-grands-evenements-historiques-de-lorraine-et-de-franche-comte",
    "https://www.republicain-lorrain.fr/sport/2026/08/26/je-donne-le-biberon-en-rentrant-la-preparation-pas-comme-les-autres-de-quentin-fillon-maillet",
    "https://www.bienpublic.com/sport/2026/08/26/claire-tomaselli-dijon-a-un-savoir-faire",
    "https://www.vosgesmatin.fr/economie/2026/08/26/gerardmer-face-a-l-afflux-de-touristes-les-agents-des-dechets-redoublent-d-efforts-tout-l-ete",
    "https://www.leprogres.fr/economie/2026/08/26/agriculture-et-secheresse-la-pire-annee-depuis-quarante-ans",
    "https://www.lalsace.fr/economie/2026/08/26/le-kougelhopf-d-or-pour-francis-jamm-decroche-lors-de-la-foire-aux-vins"
]

if not IN_GITHUB_ACTIONS:
    URLS.append("https://www.ledauphine.com/societe/2023/03/27/la-charte-editoriale-des-faits-divers-justice")


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.mark.parametrize("url", URLS)
def test_article_pages(client, url):
    id_response = client.get("/api/getId?url="+url)
    assert id_response.status_code == 200
    
    data = id_response.get_json()
    assert data['success'] is True
    
    # We doesn't care if it's the correct ID/provider as it's test by test_article_regex in test_common.py
    
    page_response = client.get(data['url'])
    
    if data['slug'] == OuestFranceArticle.SLUG and not OUESTFRANCE_ENABLED:
        # If Ouest-France is disabled and the URL is Ouest-France, expect a 501 Not Implemented
        assert page_response.status_code == 501
    elif data['slug'] == MediapartArticle.SLUG and not MEDIAPART_ENABLED:
        # If Mediapart is disabled and the URL is Mediapart, expect a 501 Not Imtplemented
        assert page_response.status_code == 501
    else:
        print(data['slug'], OUESTFRANCE_ENABLED)
        assert page_response.status_code == 200