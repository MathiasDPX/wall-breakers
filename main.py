import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

import sass
import sentry_sdk
from flask import Flask, Response, abort, render_template, request, send_file
from flask_cors import CORS
from prometheus_client import CONTENT_TYPE_LATEST
from sentry_sdk.integrations.flask import FlaskIntegration

from errors import register_error_handlers
from providers.common import get_article_from_url
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
OUESTFRANCE_ENABLED = os.getenv("OUESTFRANCE_REFRESH_TOKEN", None) != None
MEDIAPART_ENABLED = os.getenv("PIERREVIVES_USERNAME") is not None and os.getenv("PIERREVIVES_PASSWORD") is not None

build_ts = datetime.now(timezone.utc)
app = Flask(__name__)
CORS(app)
register_error_handlers(app)
sass.compile(dirname=("./static/scss/", "./static/css"))

@app.context_processor
def inject_context():
    return {
        "build_ts": build_ts,
        "git_sha": os.getenv("GITHUB_SHA", "development"),
        "debug": DEBUG,
        "is_ouestfrance_enabled": OUESTFRANCE_ENABLED,
        "is_mediapart_enabled": MEDIAPART_ENABLED
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


@app.route("/api/getId")
def redirection_api_route():
    url = request.args.get("url")
    if url is None:
        return {"success": False, "message": "No URL provided"}, 400

    provider: Article = None
    article_id = None

    started_at = time.perf_counter()
    provider, article_id = get_article_from_url(url)

    if article_id is None:
        return {
            "success": False,
            "message": "No provider found available for this URL",
        }, 404

    article_url = f"/{provider.SLUG}/{article_id}"

    return {
        "success": True,
        "provider": provider.PROVIDER,
        "id": article_id,
        "url": article_url,
        "slug": provider.SLUG,
    }


@app.route("/api/article/<slug>:<id>")
def article_api_route(slug, id):
    if slug not in ARTICLES:
        return {"success": False, "message": "Provider not found"}, 400

    article_cls = ARTICLES[slug]

    article = article_cls(id)

    return article.asdict()


@app.route("/<slug>/<id>")
def article_route(slug, id):
    article_cls = ARTICLES.get(slug)
    if article_cls is None:
        return abort(404)

    viewable = article_cls.get_readable_data != Article.get_readable_data

    article = article_cls(id)

    return render_template("article.html", article=article, viewable=viewable)

@app.route("/<slug>/<id>/raw")
def raw_article_route(slug, id):
    if not DEBUG:
        return abort(423)
        
    article_cls = ARTICLES.get(slug)
    if article_cls is None:
        return abort(404)

    article = article_cls.get_data(id)
    return article

@app.route("/<slug>/<id>/view")
def viewable_article_route(slug, id):
    if not DEBUG:
        return abort(423)
        
    article_cls = ARTICLES.get(slug)
    if article_cls is None:
        return abort(404)

    article = article_cls.get_readable_data(id)
    return article

@app.route("/")
def index_route():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
