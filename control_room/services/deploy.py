"""GitHub deploy helpers for platform owners."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.utils import timezone


class DeployError(Exception):
    """Raised when a deploy step fails."""


def _run_command(command: list[str], *, cwd: Path, timeout: int = 180) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    output = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
    if completed.returncode != 0:
        raise DeployError(output or f"Command failed: {' '.join(command)}")
    return output


def run_github_update(*, remote: str = "origin", branch: str = "main") -> dict:
    app_dir = Path(settings.BASE_DIR)
    if not (app_dir / ".git").exists():
        raise DeployError(f"{app_dir} is not a git repository.")

    logs: list[str] = []

    def step(label: str, command: list[str]) -> str:
        logs.append(f"$ {' '.join(command)}")
        result = _run_command(command, cwd=app_dir)
        if result:
            logs.append(result)
        logs.append(f"✓ {label}")
        return result

    before = _run_command(["git", "rev-parse", "--short", "HEAD"], cwd=app_dir)
    step("Fetched latest changes", ["git", "fetch", remote, branch])
    step("Pulled latest code", ["git", "pull", remote, branch])
    step("Applied migrations", [sys.executable, "manage.py", "migrate", "--noinput"])
    step("Collected static files", [sys.executable, "manage.py", "collectstatic", "--noinput"])
    after = _run_command(["git", "rev-parse", "--short", "HEAD"], cwd=app_dir)

    logs.append("")
    logs.append("Restart the app server to load new code:")
    logs.append("  sudo systemctl restart marketing-site")

    return {
        "status": "success",
        "commit_before": before,
        "commit_after": after,
        "output": "\n".join(logs),
        "finished_at": timezone.now(),
    }
