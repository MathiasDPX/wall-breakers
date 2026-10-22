from prometheus_client import Histogram, Gauge
from functools import wraps


ARTICLE_PROCESSING_TIME = Histogram("article_processing_time", "Time spent processing article", ["provider"])
UPSTREAM_REQUEST_TIME = Histogram("upstream_request_time", "Time spent fetching article data", ["provider"])
ARTICLE_REQUEST_COUNT = Gauge("article_request_count", "Number of article processed", ["provider"])

RESOLUTION_REQUEST_TIME = Histogram("resolution_request_time", "Time spent resolving an URL to its ID")
ARTICLE_RESOLUTION_REQUEST_COUNT = Gauge("article_resolution_request_count", "Number of article resolution", ["outcome"])

def upstream_request_timer(func):
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        with UPSTREAM_REQUEST_TIME.labels(provider=cls.PROVIDER).time():
            return func(cls, *args, **kwargs)

    return wrapper
