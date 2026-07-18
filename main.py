import leparisien


if __name__ == "__main__":
    article = leparisien.Article.get_from_url("https://www.leparisien.fr/sports/football/coupe-du-monde/france-angleterre-la-composition-probable-des-bleus-avec-zaire-emery-cherki-olise-et-mbappe-18-07-2026-ZMLNSNIHBVGEPALOLJ3KGMBQAI.php")
    print(article)