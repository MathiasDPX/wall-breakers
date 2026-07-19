from flask import Flask, render_template, send_file
import sass
from providers import *
import os

app = Flask(__name__)

sass.compile(dirname=('./static/scss/', './static/css'))


@app.route("/favicon.ico")
def favicon_route():
    return send_file(os.path.join("static", "images", "favicon.ico"))

@app.route("/lm/<id>")
def lemonde_route(id):
    article = LeMondeArticle(id)
    return render_template("article.html", article=article)


@app.route("/lp/<id>")
def leparisien_route(id):
    article = LeParisienArticle(id)
    return render_template("article.html", article=article)

@app.route("/")
def index_route():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)