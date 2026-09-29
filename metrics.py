import os
import time
from contextlib import contextmanager
from contextvars import ContextVar

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    multiprocess,
)

PREFIX = (os.getenv("PROMETHEUS_PREFIX") or "wallbreakers").strip().rstrip("_")
MULTIPROC_DIR = os.getenv("PROMETHEUS_MULTIPROC_DIR")

# Serving an article means a live HTTP call to the publisher, so latencies are
# counted in seconds and the buckets go up to a minute.
REQUEST_DURATION_BUCKETS = (
    0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 20, 30, 60,
)
FETCH_DURATION_BUCKETS = (
    0.05, 0.1, 0.25, 0.5, 1, 1.5, 2, 3, 5, 8, 13, 21, 34, 60,
)
CONTENT_SIZE_BUCKETS = (
    1e3, 5e3, 1e4, 2.5e4, 5e4, 1e5, 2.5e5, 5e5, 1e6, 2.5e6,
)
CONTENT_BLOCKS_BUCKETS = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)

# --- HTTP -------------------------------------------------------------------

REQUESTS = Counter(
    f"{PREFIX}_http_requests_total",
    "HTTP requests served, by route, method and status code.",
    ["method", "route", "code"],
)
REQUESTS_IN_PROGRESS = Gauge(
    f"{PREFIX}_http_requests_in_progress",
    "HTTP requests currently being served.",
    ["route"],
    multiprocess_mode="livesum",
)
REQUEST_DURATION = Histogram(
    f"{PREFIX}_http_request_duration_seconds",
    "Time spent serving an HTTP request, fetching and rendering included.",
    ["method", "route"],
    buckets=REQUEST_DURATION_BUCKETS,
)
RESPONSE_SIZE = Histogram(
    f"{PREFIX}_http_response_size_bytes",
    "Size of the response body sent to the client.",
    ["method", "route"],
    buckets=CONTENT_SIZE_BUCKETS,
)

# --- Articles ---------------------------------------------------------------

ARTICLE_FETCHES = Counter(
    f"{PREFIX}_article_fetches_total",
    "Articles fetched from a publisher, by provider and outcome.",
    ["provider", "outcome"],
)
ARTICLE_FETCH_DURATION = Histogram(
    f"{PREFIX}_article_fetch_duration_seconds",
    "Time spent fetching and parsing an article.",
    ["provider"],
    buckets=FETCH_DURATION_BUCKETS,
)
ARTICLE_CONTENT_SIZE = Histogram(
    f"{PREFIX}_article_content_size_bytes",
    "Size of the sanitized article content.",
    ["provider"],
    buckets=CONTENT_SIZE_BUCKETS,
)
ARTICLE_CONTENT_BLOCKS = Histogram(
    f"{PREFIX}_article_content_blocks",
    "Number of content blocks in an article.",
    ["provider"],
    buckets=CONTENT_BLOCKS_BUCKETS,
)
ARTICLE_READABLE = Counter(
    f"{PREFIX}_article_readable_total",
    "Articles served, by provider and whether a readable version exists.",
    ["provider", "readable"],
)
ARTICLE_ERRORS = Counter(
    f"{PREFIX}_article_errors_total",
    "Article fetching errors, by provider and error type.",
    ["provider", "error"],
)

# URL resolution

URL_RESOLUTIONS = Counter(
    f"{PREFIX}_url_resolutions_total",
    "Calls to the /api/getId endpoint, by result.",
    ["result"],
)
URL_RESOLUTION_DURATION = Histogram(
    f"{PREFIX}_url_resolution_duration_seconds",
    "Time spent matching an URL against every known publisher.",
    buckets=REQUEST_DURATION_BUCKETS,
)

# Scraping quality

UNHANDLED_BLOCKS = Counter(
    f"{PREFIX}_unhandled_blocks_total",
    "Content blocks no provider knows how to render, by provider and block type.",
    ["provider", "block_type"],
)

# Build

BUILD_INFO = Info(f"{PREFIX}_build", "Version, git revision and runtime environment.")


_current_provider: ContextVar[str] = ContextVar("wallbreakers_current_provider", default="unknown")


def current_provider() -> str:
    """Provider currently being parsed, or ``unknown`` outside of a fetch."""
    return _current_provider.get()


def set_build_info(**labels) -> None:
    BUILD_INFO.info({key: str(value) for key, value in labels.items()})


def record_unhandled_block(block_type: str) -> None:
    UNHANDLED_BLOCKS.labels(
        provider=current_provider(), block_type=block_type
    ).inc()


class FetchTracker:
    """Collects the metrics of a single ``Article(provider, id)`` call."""

    def __init__(self, provider: str):
        self.provider = provider

    def article(self, article) -> None:
        """Record the size and the shape of a freshly built article."""
        content = article.content
        if isinstance(content, (list, tuple)):
            blocks = len(content)
            size = sum(len(str(block).encode("utf-8")) for block in content)
        else:
            blocks = 1
            size = len(str(content).encode("utf-8"))

        ARTICLE_CONTENT_SIZE.labels(provider=self.provider).observe(size)
        ARTICLE_CONTENT_BLOCKS.labels(provider=self.provider).observe(blocks)

    def readable(self, is_readable: bool) -> None:
        ARTICLE_READABLE.labels(
            provider=self.provider, readable=str(is_readable).lower()
        ).inc()


@contextmanager
def track_fetch(provider: str):
    """Time an article fetch, count its outcome and tag nested errors."""

    token = _current_provider.set(provider)
    started_at = time.perf_counter()

    try:
        yield FetchTracker(provider)
    except Exception as error:
        ARTICLE_FETCHES.labels(provider=provider, outcome="error").inc()
        ARTICLE_ERRORS.labels(
            provider=provider, error=type(error).__name__
        ).inc()
        raise
    else:
        ARTICLE_FETCHES.labels(provider=provider, outcome="success").inc()
    finally:
        ARTICLE_FETCH_DURATION.labels(provider=provider).observe(
            time.perf_counter() - started_at
        )
        _current_provider.reset(token)


def record_url_resolution(result: str, duration: float | None = None) -> None:
    URL_RESOLUTIONS.labels(result=result).inc()
    if duration is not None:
        URL_RESOLUTION_DURATION.observe(duration)


def _registry():
    """Registry to render, or ``None`` to use the default in-process one."""
    if not MULTIPROC_DIR:
        return None

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return registry


def render() -> bytes:
    registry = _registry()
    return generate_latest() if registry is None else generate_latest(registry)


def init_app(app) -> None:
    """Instrument every request of a Flask app."""
    from flask import g, request

    def route() -> str:
        return request.url_rule.rule if request.url_rule else "unmatched"

    @app.before_request
    def start_request() -> None:
        g.metrics_started_at = time.perf_counter()
        g.metrics_in_flight = True
        REQUESTS_IN_PROGRESS.labels(route=route()).inc()

    @app.after_request
    def observe_request(response):
        started_at = g.get("metrics_started_at")
        if started_at is not None:
            REQUEST_DURATION.labels(
                method=request.method, route=route()
            ).observe(time.perf_counter() - started_at)

        REQUESTS.labels(
            method=request.method, route=route(), code=response.status_code
        ).inc()
        RESPONSE_SIZE.labels(method=request.method, route=route()).observe(
            response.calculate_content_length() or 0
        )
        return response

    @app.teardown_request
    def release_request(exception=None) -> None:
        # Runs exactly once per request, whatever the outcome, so it's the only
        # safe place to release the in-flight gauge.
        if g.pop("metrics_in_flight", False):
            REQUESTS_IN_PROGRESS.labels(route=route()).dec()
