import os

from prometheus_client import Counter, Summary

METRICS_PREFIX = os.getenv("PROMETHEUS_PREFIX", "wallbreakers")

PAGE_VIEWS = Counter(METRICS_PREFIX+"_page_views", "Total number of page views", ["namespace"])
RESPONSE_TIME = Summary(METRICS_PREFIX+"_request_processing_seconds", "Time spent processing request", ["provider"])