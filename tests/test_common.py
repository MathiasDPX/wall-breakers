from providers import LeMondeArticle, LeParisienArticle

def test_leparisien_regex():
    lp_link = "https://www.leparisien.fr/sports/football/coupe-du-monde/france-angleterre-la-composition-probable-des-bleus-avec-zaire-emery-cherki-olise-et-mbappe-18-07-2026-ZMLNSNIHBVGEPALOLJ3KGMBQAI.php"

    assert LeParisienArticle.get_id_from_url(lp_link) == "ZMLNSNIHBVGEPALOLJ3KGMBQAI"
    assert LeMondeArticle.get_id_from_url(lp_link) is None


def test_lemonde_regex():
    lm_link = "https://www.lemonde.fr/planete/article/2026/07/18/au-canada-les-feux-a-repetition-bouleversent-la-foret-boreale_6724998_3244.html"

    assert LeParisienArticle.get_id_from_url(lm_link) is None
    assert LeMondeArticle.get_id_from_url(lm_link) == "6724998"
