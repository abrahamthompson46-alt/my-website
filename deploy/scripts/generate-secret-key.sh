#!/usr/bin/env bash
# Helper: generate a Django secret key for .env
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
