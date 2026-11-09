import os
import shutil

from dotenv import load_dotenv

load_dotenv()

from prometheus_client import multiprocess

bind = "0.0.0.0:8000"
accesslog = "-"
errorlog = "-"

worker_class = "gthread"
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "8"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))


def on_starting(server):
    path = os.getenv("PROMETHEUS_MULTIPROC_DIR")
    if not path:
        return

    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
