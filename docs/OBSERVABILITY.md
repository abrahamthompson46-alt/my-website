# Observability (P2-08 / P2-09)

Structured logging and Prometheus metrics for production operations.

## Structured logging

Set `LOG_FORMAT=json` (default in production when unset) to emit one JSON object per log line:

```json
{
  "timestamp": "2026-09-14T19:00:00.123456Z",
  "level": "INFO",
  "logger": "payments",
  "message": "Webhook accepted",
  "request_id": "a1b2c3d4-..."
}
```

| Variable | Purpose | Default |
|----------|---------|---------|
| `LOG_FORMAT` | `json` or `text` | `text` locally; `json` in production when unset |
| `LOG_LEVEL` | Root/app log level | `INFO` |
| `LOG_DIR` | Rotating file directory | `logs/` |

Every request gets `X-Request-ID` (echoes inbound header or generates a UUID). The same ID is attached to log records via contextvars.

### Log shipping

Ship **stdout** (JSON) from Gunicorn/Celery to your aggregator:

- journald / Docker logging driver
- Filebeat / Fluent Bit → Elasticsearch / Loki / CloudWatch
- Hosted APM already covered optionally via `SENTRY_DSN`

No vendor agent is bundled; the app emits shippable logs.

## Prometheus metrics

| Variable | Purpose | Default |
|----------|---------|---------|
| `METRICS_ENABLED` | Expose `/metrics/` | `False` |
| `METRICS_TOKEN` | Required bearer/query token when set | empty |

Enable on the VPS:

```bash
METRICS_ENABLED=1
METRICS_TOKEN=$(openssl rand -hex 24)
```

Scrape example:

```yaml
scrape_configs:
  - job_name: zreta
    metrics_path: /metrics/
    authorization:
      credentials: "<METRICS_TOKEN>"
    static_configs:
      - targets: ["127.0.0.1:8000"]
```

### Series

- `zreta_http_requests_total{method,status}`
- `zreta_http_request_duration_seconds{method}`
- `zreta_webhook_events_total{gateway,result}`
- `zreta_email_events_total{result}`

Grafana: import a simple dashboard on these four series; host Grafana separately (not shipped in-repo).
