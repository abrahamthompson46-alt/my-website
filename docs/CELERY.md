# Celery background workers (P2-06 / P2-07)

Zreta uses **Celery + Redis** for async email delivery and payment webhook processing.

## Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `REDIS_URL` | Django cache/sessions (usually `/0`) | required in production |
| `CELERY_BROKER_URL` | Celery broker | derived as Redis `/1` from `REDIS_URL` |
| `CELERY_RESULT_BACKEND` | Optional result store | unset (results ignored) |
| `CELERY_TASK_ALWAYS_EAGER` | Run tasks inline (tests/dev) | `False` |

Example:

```bash
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
```

## Local / Docker

```bash
docker compose up redis worker -d
# or
celery -A config worker --loglevel=INFO
```

Without a worker, set `CELERY_TASK_ALWAYS_EAGER=1` so email/webhooks still run inline.

## Production (systemd)

```bash
sudo cp deploy/systemd/zreta-celery.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now zreta-celery
sudo systemctl status zreta-celery
```

After `pip install -r requirements/base.txt` (or production), restart both Gunicorn and the Celery worker.

## Behavior

- **Email:** `queue_platform_mail()` sends via Celery when async mode is on; otherwise inline.
- **Webhooks:** `enqueue_process_webhook()` returns HTTP **202 accepted** when queued; otherwise processes synchronously and returns **200/400** as before.
- **Tests:** `config.settings.test` forces `CELERY_TASK_ALWAYS_EAGER=True`.
