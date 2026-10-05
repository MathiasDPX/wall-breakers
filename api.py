import os

from flask import Blueprint, abort, jsonify, request

from providers.common import get_article_from_url
from providers.registry import ARTICLES, PROVIDERS

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _api_success(data, status=200, cache_control=None):
    response = jsonify({"success": True, "data": data})
    response.status_code = status
    if cache_control:
        response.headers["Cache-Control"] = cache_control
    return response


def _extract_request_url():
    url = None
    if request.method == "POST":
        if request.is_json:
            body = request.get_json(silent=True) or {}
            if isinstance(body, dict):
                url = body.get("url")
        if url is None:
            url = request.form.get("url")
    if url is None:
        url = request.args.get("url")
    if url is None:
        abort(400, description="No URL provided")
    url = url.strip()
    if not url:
        abort(400, description="No URL provided")
    if not (url.startswith("http://") or url.startswith("https://")):
        abort(400, description="URL must start with http:// or https://")
    return url


@api_bp.route("/getId", methods=["GET", "POST"])
def redirection_api_route():
    url = _extract_request_url()

    provider, article_id = get_article_from_url(url)

    if article_id is None:
        abort(404, description="No provider found available for this URL")

    return _api_success(
        {
            "provider": {"name": provider.PROVIDER, "slug": provider.SLUG},
            "id": article_id,
            "page_url": f"/{provider.SLUG}/{article_id}",
            "api_url": f"/api/article/{provider.SLUG}/{article_id}",
        },
        cache_control="public, max-age=86400",
    )


@api_bp.route("/article/<slug>/<path:id>")
def article_api_route(slug, id):
    slug = (slug or "").strip().lower()
    id = (id or "").strip()
    if not id:
        abort(400, description="Article id must not be empty")
    if slug not in ARTICLES:
        abort(404, description="Provider not found")

    article_cls = ARTICLES[slug]

    article = article_cls(id)

    return _api_success(
        article.asdict(),
        cache_control="public, max-age=300, stale-while-revalidate=600",
    )


@api_bp.route("/providers")
def providers_api_route():
    providers = sorted(
        (
            {
                "slug": provider.SLUG,
                "name": provider.PROVIDER,
                "group": provider.GROUP,
                "enabled": provider.is_enabled(),
            }
            for provider in PROVIDERS
        ),
        key=lambda item: item["name"].lower(),
    )
    return _api_success(
        providers,
        cache_control="public, max-age=60",
    )


@api_bp.route("/health")
def health_api_route():
    return _api_success(
        {
            "status": "ok",
            "version": "1.1.0",
            "git_sha": os.getenv("GITHUB_SHA", "development"),
        },
        cache_control="no-store",
    )
