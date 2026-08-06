"""Gunicorn configuration for the marketing website (systemd)."""

import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "unix:/run/zreta/gunicorn.sock")
workers = int(os.environ.get("GUNICORN_WORKERS", max(2, multiprocessing.cpu_count() * 2 + 1)))
threads = int(os.environ.get("GUNICORN_THREADS", 1))
worker_class = "sync"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 60))
graceful_timeout = 30
keepalive = 5
umask = 0o007
user = os.environ.get("GUNICORN_USER", "marketing")
group = os.environ.get("GUNICORN_GROUP", "www-data")
max_requests = 1000
max_requests_jitter = 50
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "/var/log/marketing-site/gunicorn-access.log")
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "/var/log/marketing-site/gunicorn-error.log")
capture_output = True
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
proc_name = "marketing-site"
