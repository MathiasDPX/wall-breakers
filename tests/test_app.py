import os

import pytest
from dotenv import load_dotenv

from main import app
from providers.registry import *

load_dotenv()

OUESTFRANCE_ENABLED = os.getenv("OUESTFRANCE_REFRESH_TOKEN", None) != None

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
    "https://www.ouest-france.fr/societe/ruralites/tu-es-un-peu-le-maire-sans-lecharpe-les-secretaires-de-mairie-espece-en-voie-de-disparition-1b28e6b2-66d4-11f0-bb8e-c5b2af864a8a"
]


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
    else:
        print(data['slug'], OUESTFRANCE_ENABLED)
        assert page_response.status_code == 200