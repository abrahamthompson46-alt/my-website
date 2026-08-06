"""
Environment variable loader using django-environ.
Reads from .env file at project root when present.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    DJANGO_DEBUG=(bool, False),
    DB_CONN_MAX_AGE=(int, 600),
    LOG_LEVEL=(str, "INFO"),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))
