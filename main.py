from flask import Flask, render_template, send_file, request, abort
import sass
from providers import *
import os

app = Flask(__name__)

sass.compile(dirname=('./static/scss/', './static/css'))

ARTICLES = {
    LeMondeArticle.SLUG: LeMondeArticle,
    LeTelegrammeArticle.SLUG: LeTelegrammeArticle,
    LeParisienArticle.SLUG: LeParisienArticle,
    LesEchosArticle.SLUG: LesEchosArticle
}


@app.route("/favicon.ico")
def favicon_route():
    return send_file(os.path.join("static", "images", "favicon.ico"))

@app.route("/api/getId")
def redirection_route():
    url = request.args.get("url")
    if url == None:
        return {
            "success": False,
            "message": "No URL provided"
        }
    
    lp_id = LeParisienArticle.get_id_from_url(url)
    lm_id = LeMondeArticle.get_id_from_url(url)
    lt_id = LeTelegrammeArticle.get_id_from_url(url)
    le_id = LesEchosArticle.get_id_from_url(url)
    
    if lp_id is None and lm_id is None and lt_id is None and le_id is None:
        return {
            "success": False,
            "message": "No provider found available for this URL"
        }
    
    provider = "unkown"
    article_id = "unknown"
    url = "/"
    
    if lp_id is not None:
        provider = "Le Parisien"
        article_id = lp_id
        url = "/lp/"+article_id
    elif lm_id is not None:
        provider = "Le Monde"
        article_id = lm_id
        url = "/lm/"+article_id
    elif lt_id is not None:
        provider = "Le Télégramme"
        article_id = lt_id
        url = "/lt/"+article_id
    elif le_id is not None:
        provider = "Les Echos"
        article_id = le_id
        url = "/le/"+article_id
    
    return {
        "success": True,
        "provider": provider,
        "id": article_id,
        "url": url
    }

@app.route("/<slug>/<id>")
def article_route(slug, id):
    article_cls = ARTICLES.get(slug)
    if article_cls is None:
        abort(404)

    article = article_cls(id)
    return render_template("article.html", article=article)

@app.route("/")
def index_route():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)