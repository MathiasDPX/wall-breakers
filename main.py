import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

import sass
import sentry_sdk
from flask import Flask, Response, abort, g, render_template, request, send_file
from flask_cors import CORS
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sentry_sdk.integrations.flask import FlaskIntegration

from errors import register_error_handlers
from metrics import (
    ARTICLE_ENDPOINTS,
    articles_served_total,
    http_request_duration_seconds,
    http_requests_total,
    init_metrics,
    normalize_endpoint,
    normalize_source,
    record_provider_error,
    url_resolution_duration_seconds,
    url_resolutions_total,
)
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

build_ts = datetime.now(timezone.utc)
app = Flask(__name__)
CORS(app)
register_error_handlers(app)
init_metrics(app)
sass.compile(dirname=("./static/scss/", "./static/css"))

@app.before_request
def metrics_before_request():
    g.wallbreakers_start = time.perf_counter()


@app.after_request
def metrics_after_request(response):
    elapsed = time.perf_counter() - g.get("wallbreakers_start", time.perf_counter())
    endpoint = normalize_endpoint(request.url_rule)
    http_requests_total.labels(
        method=request.method, endpoint=endpoint, status=str(response.status_code)
    ).inc()
    provider = ""
    if (
        request.url_rule is not None
        and request.url_rule.endpoint in ARTICLE_ENDPOINTS
        and (request.view_args or {}).get("slug") in ARTICLES
    ):
        provider = request.view_args["slug"]
    http_request_duration_seconds.labels(endpoint=endpoint, provider=provider).observe(
        elapsed
    )
    return response


@app.route("/metrics")
def metrics_route():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

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


@app.route("/api/getId")
def redirection_api_route():
    url = request.args.get("url")
    if url is None:
        return {"success": False, "message": "No URL provided"}, 400

    source = normalize_source(request.headers.get("X-Wallbreakers-Client", "unknown"))

    started_at = time.perf_counter()
    provider, article_id = get_article_from_url(url)
    url_resolution_duration_seconds.labels(source=source).observe(
        time.perf_counter() - started_at
    )

    if article_id is None:
        url_resolutions_total.labels(
            provider="none", source=source, result="not_found"
        ).inc()
        return {
            "success": False,
            "message": "No provider found available for this URL",
        }, 404

    url_resolutions_total.labels(
        provider=provider.SLUG, source=source, result="found"
    ).inc()
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

    try:
        article = article_cls(id)
    except Exception as exc:
        record_provider_error(slug, exc)
        articles_served_total.labels(provider=slug, route="api", status="error").inc()
        raise
    articles_served_total.labels(provider=slug, route="api", status="success").inc()

    return article.asdict()


@app.route("/<slug>/<id>")
def article_route(slug, id):
    article_cls = ARTICLES.get(slug)
    if article_cls is None:
        return abort(404)

    viewable = article_cls.get_readable_data != Article.get_readable_data

    try:
        article = article_cls(id)
    except Exception as exc:
        record_provider_error(slug, exc)
        articles_served_total.labels(provider=slug, route="html", status="error").inc()
        raise
    articles_served_total.labels(provider=slug, route="html", status="success").inc()

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
    return render_template("index.html", sources=get_sources())


if __name__ == "__main__":
    app.run(debug=True)
