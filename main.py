import os
from datetime import datetime, timezone

import sass
import sentry_sdk
from flask import Flask, abort, render_template, request, send_file
from flask_cors import CORS
from requests.exceptions import HTTPError
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

from providers.nytimes import DataDomeCookieExpiredError
from providers import *

load_dotenv()

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        integrations=[FlaskIntegration()],
        ignore_errors=[KeyboardInterrupt],
        enable_logs=True,
    )

build_ts = datetime.now(timezone.utc)
app = Flask(__name__)
CORS(app)
sass.compile(dirname=("./static/scss/", "./static/css"))

@app.context_processor
def inject_context():
    return {
        "build_ts": build_ts,
        "git_sha": os.getenv("GITHUB_SHA", "development")
    }

@app.errorhandler(HTTPException)
def handle_exception(e):
    return render_template("error.html", code=e.code, name=e.name, description=e.description), e.code

@app.errorhandler(HTTPError)
def handle_api_exception(e):
    return {"success": False, "message": e.response.reason}, e.response.status_code


@app.errorhandler(DataDomeCookieExpiredError)
def handle_datadome_exception(e):
    return render_template("error.html", code=503, name="Service Unavailable", description="The service is temporarily unavailable due to an expired DataDome token."), 503


@app.route("/favicon.ico")
def favicon_route():
    return send_file(os.path.join("static", "images", "favicon.ico"))


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
    article_url = None

    for cls in PROVIDERS:
        article_id = cls.get_id_from_url(url)

        if article_id is not None:
            provider = cls
            article_url = f"/{cls.SLUG}/{article_id}"
            break

    if article_id is None:
        return {
            "success": False,
            "message": "No provider found available for this URL",
        }, 404

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

    article: Article = ARTICLES[slug](id)

    return article.asdict()


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
    app.run(debug=False)
