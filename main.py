from flask import Flask, render_template, send_file, request, abort
import sass
from providers import *
import os

app = Flask(__name__)

sass.compile(dirname=('./static/scss/', './static/css'))


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

    provider = None
    article_id = None
    article_url = None

    for cls in PROVIDERS:
        article_id = cls.get_id_from_url(url)
        
        if article_id is not None:
            provider = cls.PROVIDER
            article_url = f"/{cls.SLUG}/{article_id}"
            break

    if article_id is None:
        return {
            "success": False,
            "message": "No provider found available for this URL"
        }
    
    return {
        "success": True,
        "provider": provider,
        "id": article_id,
        "url": article_url
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