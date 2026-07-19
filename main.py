from flask import Flask, render_template
import sass
from providers import *

app = Flask(__name__)

sass.compile(dirname=('./static/scss/', './static/css'))


@app.route("/lm/<id>")
def lemonde_route(id):
    article = LeMondeArticle(id)
    return render_template("article.html", article=article)


@app.route("/lp/<id>")
def leparisien_route(id):
    article = LeParisienArticle(id)
    return render_template("article.html", article=article)

if __name__ == "__main__":
    app.run(debug=True)