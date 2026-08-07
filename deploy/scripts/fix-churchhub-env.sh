#!/usr/bin/env bash
# Fix ChurchHub .env ALLOWED_HOSTS and CSRF origins (remove markdown link syntax).
# Run on VPS:
#   sudo bash /path/to/fix-churchhub-env.sh
set -euo pipefail

ENV_FILE="${CHURCHHUB_ENV:-/home/churchhub/apps/churchhub/.env}"
SERVICE_NAME="${CHURCHHUB_SERVICE:-churchhub}"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: $ENV_FILE not found"
    exit 1
fi

BACKUP="${ENV_FILE}.bak-$(date +%Y%m%d%H%M%S)"
cp "$ENV_FILE" "$BACKUP"
echo "Backup: $BACKUP"

ENV_FILE="$ENV_FILE" python3 <<'PY'
from pathlib import Path
import os
import re

path = Path(os.environ["ENV_FILE"])
text = path.read_text(encoding="utf-8")

allowed = "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,162.35.179.20,zreta.com,www.zreta.com,app.zreta.com"
csrf = "DJANGO_CSRF_TRUSTED_ORIGINS=https://zreta.com,https://www.zreta.com,https://app.zreta.com"

def set_var(name, line, content):
    pattern = re.compile(rf"^\s*{re.escape(name)}\s*=.*$", re.MULTILINE)
    if pattern.search(content):
        return pattern.sub(line, content, count=1)
    if content and not content.endswith("\n"):
        content += "\n"
    return content + line + "\n"

text = set_var("DJANGO_ALLOWED_HOSTS", allowed, text)
text = set_var("DJANGO_CSRF_TRUSTED_ORIGINS", csrf, text)
path.write_text(text, encoding="utf-8")
PY

echo "==> Updated values:"
grep -E "^DJANGO_ALLOWED_HOSTS=|^DJANGO_CSRF_TRUSTED_ORIGINS=" "$ENV_FILE"

echo "==> Restarting $SERVICE_NAME ..."
systemctl restart "$SERVICE_NAME"
sleep 2
systemctl is-active --quiet "$SERVICE_NAME" && echo "Service $SERVICE_NAME is active." || {
    echo "ERROR: $SERVICE_NAME failed to start. Check: journalctl -u $SERVICE_NAME -n 50"
    exit 1
}

echo "Done."
