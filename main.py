import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

import sass
import sentry_sdk
from flask import Flask, abort, render_template, send_file
from flask_cors import CORS
from sentry_sdk.integrations.flask import FlaskIntegration

from api import api_bp
from errors import register_error_handlers
from providers.registry import *

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        integrations=[FlaskIntegration()],
        ignore_errors=[KeyboardInterrupt],
        enable_logs=True,
    )
    
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

build_ts = datetime.now(timezone.utc)
app = Flask(__name__)
CORS(app)
register_error_handlers(app)
app.register_blueprint(api_bp)
sass.compile(dirname=("./static/scss/", "./static/css"))

@app.context_processor
def inject_context():
    return {
        "build_ts": build_ts,
        "git_sha": os.getenv("GITHUB_SHA", "development"),
        "debug": DEBUG,
    }
    

@app.route("/favicon.ico")
def favicon_route():
    return send_file(os.path.join("static", "images", "favicon.ico"))

@app.route("/redirect.user.js")
def userscript_route():
    return send_file(os.path.join("static", "userscript.js"))

@app.route("/openapi.yml")
def openapi_route():
    return send_file(
        os.path.join("static", "openapi.yml"),
        mimetype="text/plain",
        as_attachment=False,
    )


@app.route("/<slug>/<path:id>")
def article_route(slug, id):
    slug = (slug or "").strip().lower()
    article_cls = ARTICLES.get(slug)
    if article_cls is None:
        return abort(404)

    viewable = article_cls.get_readable_data != Article.get_readable_data

    article = article_cls(id)

    return render_template("article.html", article=article, viewable=viewable)

@app.route("/<slug>/<path:id>/raw")
def raw_article_route(slug, id):
    if not DEBUG:
        return abort(423)

    slug = (slug or "").strip().lower()
    article_cls = ARTICLES.get(slug)
    if article_cls is None:
        return abort(404)

    article = article_cls.get_data(id)
    return article

@app.route("/<slug>/<path:id>/view")
def viewable_article_route(slug, id):
    if not DEBUG:
        return abort(423)

    slug = (slug or "").strip().lower()
    article_cls = ARTICLES.get(slug)
    if article_cls is None:
        return abort(404)

    article = article_cls.get_readable_data(id)
    return article

@app.route("/")
def index_route():
    return render_template("index.html", sources=get_sources())


if __name__ == "__main__":
    app.run(debug=True)
