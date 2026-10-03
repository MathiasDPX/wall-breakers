import functools
import os
import time
from contextvars import ContextVar

import requests
from prometheus_client import Counter, Gauge, Histogram

FETCH_BUCKETS = [0.1, 0.25, 0.5, 1, 2.5, 5, 10]
HTTP_BUCKETS = [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
RESOLUTION_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1]

http_requests_total = Counter(
    "wallbreakers_http_requests_total",
    "Total HTTP requests served.",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "wallbreakers_http_request_duration_seconds",
    "Total HTTP request latency (fetch + render).",
    ["endpoint", "provider"],
    buckets=HTTP_BUCKETS,
)

articles_served_total = Counter(
    "wallbreakers_articles_served_total",
    "Articles served to readers.",
    ["provider", "route", "status"],
)

article_fetch_duration_seconds = Histogram(
    "wallbreakers_article_fetch_duration_seconds",
    "Upstream fetch time alone (provider get_data).",
    ["provider"],
    buckets=FETCH_BUCKETS,
)

url_resolutions_total = Counter(
    "wallbreakers_url_resolutions_total",
    "URL -> provider resolutions.",
    ["provider", "source", "result"],
)

url_resolution_duration_seconds = Histogram(
    "wallbreakers_url_resolution_duration_seconds",
    "URL resolution time.",
    ["source"],
    buckets=RESOLUTION_BUCKETS,
)

provider_errors_total = Counter(
    "wallbreakers_provider_errors_total",
    "Provider failures by mapped error type.",
    ["provider", "error_type"],
)

upstream_requests_total = Counter(
    "wallbreakers_upstream_requests_total",
    "Upstream HTTP calls made to providers.",
    ["provider", "status_code"],
)

upstream_duration_seconds = Histogram(
    "wallbreakers_upstream_duration_seconds",
    "Upstream HTTP call duration.",
    ["provider"],
    buckets=FETCH_BUCKETS,
)

build_info = Gauge(
    "wallbreakers_build_info",
    "Build info.",
    ["git_sha"],
)

_current_provider: ContextVar = ContextVar("wallbreakers_provider", default=None)



def normalize_source(raw) -> str:
    """Normalize the ``X-Wallbreakers-Client`` header to site|extension|unknown."""
    value = (raw or "unknown").strip().lower()
    if value == "site":
        return "site"
    if value in ("extension", "userscript", "user-script", "user_script"):
        return "extension"
    return "unknown"



ENDPOINT_LABELS = {
    "index_route": "/",
    "redirection_api_route": "/api/getId",
    "article_api_route": "/api/article",
    "article_route": "/article_page",
    "raw_article_route": "/article_raw",
    "viewable_article_route": "/article_view",
    "metrics_route": "/metrics",
    "favicon_route": "/favicon.ico",
    "userscript_route": "/redirect.user.js",
    "openapi_route": "/openapi.yml",
}

ARTICLE_ENDPOINTS = {"article_api_route", "article_route"}


def normalize_endpoint(url_rule) -> str:
    if url_rule is None:
        return "unknown"
    return ENDPOINT_LABELS.get(url_rule.endpoint, "unknown")


def map_exception_to_error_type(exc: BaseException) -> str:
    """Map business exceptions from errors.py to a bounded error_type label."""
    from providers.exceptions import (
        DataDomeCookieExpiredError,
        MediapartDisabledException,
        MediapartInvalidLogin,
        OuestFranceDisabledException,
        OuestFranceMissingSubscriptionException,
        SocialterDisabledException,
        SocialterLayoutError,
        SocialterMissingSubscriptionException,
        SocialterRegistrationError,
        SocialterThrottledException,
    )

    if isinstance(exc, DataDomeCookieExpiredError):
        return "datadome_503"
    if isinstance(
        exc,
        (
            OuestFranceDisabledException,
            MediapartDisabledException,
            SocialterDisabledException,
            NotImplementedError,
        ),
    ):
        return "disabled_501"
    if isinstance(
        exc,
        (
            OuestFranceMissingSubscriptionException,
            MediapartInvalidLogin,
            SocialterMissingSubscriptionException,
        ),
    ):
        return "no_subscription_402"
    if isinstance(exc, SocialterThrottledException):
        return "throttled_429"
    if isinstance(exc, SocialterLayoutError):
        return "parse_error"
    if isinstance(exc, SocialterRegistrationError):
        return "upstream_5xx"
    if isinstance(exc, requests.HTTPError):
        status = None
        response = getattr(exc, "response", None)
        if response is not None:
            status = getattr(response, "status_code", None)
        if isinstance(status, int) and 400 <= status <= 499:
            return "upstream_4xx"
        return "upstream_5xx"
    if isinstance(exc, requests.Timeout):
        return "timeout"
    return "parse_error"


def record_provider_error(provider: str, exc: BaseException) -> str:
    """Increment provider_errors_total once per exception (deduplicated).

    Returns the error_type used.
    """
    if getattr(exc, "_wallbreakers_counted", False):
        return getattr(exc, "_wallbreakers_error_type", "parse_error")
    error_type = map_exception_to_error_type(exc)
    provider_errors_total.labels(provider=provider, error_type=error_type).inc()
    exc._wallbreakers_counted = True
    exc._wallbreakers_error_type = error_type
    return error_type


def _wrap_get_data(cls):
    slug = cls.SLUG
    original = cls.get_data
    if getattr(original, "__wallbreakers_wrapped__", False):
        return

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        token = _current_provider.set(slug)
        start = time.perf_counter()
        try:
            return original(*args, **kwargs)
        except Exception as exc:
            article_fetch_duration_seconds.labels(provider=slug).observe(
                time.perf_counter() - start
            )
            record_provider_error(slug, exc)
            raise
        finally:
            _current_provider.reset(token)

    wrapper.__wallbreakers_wrapped__ = True
    setattr(cls, "get_data", staticmethod(wrapper))


def _patch_requests():
    session_request = requests.sessions.Session.request
    if getattr(session_request, "__wallbreakers_wrapped__", False):
        return

    @functools.wraps(session_request)
    def wrapper(self, method, url, **kwargs):
        provider = _current_provider.get()
        if provider is None:
            return session_request(self, method, url, **kwargs)
        start = time.perf_counter()
        try:
            response = session_request(self, method, url, **kwargs)
        except requests.Timeout:
            upstream_requests_total.labels(
                provider=provider, status_code="timeout"
            ).inc()
            upstream_duration_seconds.labels(provider=provider).observe(
                time.perf_counter() - start
            )
            raise
        except requests.RequestException:
            upstream_requests_total.labels(
                provider=provider, status_code="error"
            ).inc()
            upstream_duration_seconds.labels(provider=provider).observe(
                time.perf_counter() - start
            )
            raise
        upstream_requests_total.labels(
            provider=provider, status_code=str(response.status_code)
        ).inc()
        upstream_duration_seconds.labels(provider=provider).observe(
            time.perf_counter() - start
        )
        return response

    wrapper.__wallbreakers_wrapped__ = True
    requests.sessions.Session.request = wrapper


def init_metrics(app=None):
    """Wire all provider instrumentation. Safe to call once at startup."""
    from providers.registry import PROVIDERS

    build_info.labels(git_sha=os.getenv("GITHUB_SHA", "development")).set(1)
    _patch_requests()
    for provider_cls in PROVIDERS:
        _wrap_get_data(provider_cls)
    return None
