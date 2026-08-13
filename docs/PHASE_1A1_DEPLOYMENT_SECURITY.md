# Phase 1A.1 — Deployment Security

**Date:** 2026-08-13  
**Status:** VERIFIED  
**Audit reference:** SEC-003 — Web UI git pull deploy via subprocess

---

## Original risk

Platform owners could POST to Control Room → Platform Ops and trigger:

```
git fetch / git pull
python manage.py migrate
python manage.py collectstatic
```

via `subprocess.run()` inside the running Django process. Any compromise of an owner session, CSRF bypass, or permission misconfiguration could lead to arbitrary code execution on the server as the app user.

---

## Root cause

`control_room/services/deploy.py` implemented `run_github_update()` and was invoked from `PlatformOpsView.post()` when `action=deploy`. The UI exposed a “Pull latest from GitHub” form at `/control/platform-ops/`.

### Flow (removed)

```
POST /control/platform-ops/  (action=deploy)
  → PlatformOpsView (PlatformOwnerMixin — staff + manage_platform_operations)
  → PlatformDeploySettingsForm validation + confirm_deploy checkbox
  → run_github_update(remote, branch)
  → subprocess.run(["git", "fetch", ...])
  → subprocess.run(["git", "pull", ...])
  → subprocess.run([python, "manage.py", "migrate", ...])
  → subprocess.run([python, "manage.py", "collectstatic", ...])
  → log_control_change(action="deploy")
  → PlatformOperationsSettings.last_deploy_* updated
```

---

## Why web deploy was not required

The repository already ships VPS deployment scripts:

- `deploy/scripts/deploy-app.sh` — migrate, collectstatic, restart Gunicorn
- `deploy/scripts/first-deploy-zreta.sh` — first-time zreta.com setup
- Documented runbooks: `docs/DEPLOYMENT-ZRETA.md`

Production env templates use local filesystem media and do not depend on in-app git pull.

---

## Changes made

| File | Change |
|------|--------|
| `control_room/services/deploy.py` | **Deleted** — subprocess deploy helper removed |
| `control_room/owner_views.py` | Removed deploy execution; `action=deploy` returns error + audit log `deploy_blocked` |
| `control_room/forms.py` | Removed `PlatformDeploySettingsForm` |
| `templates/control_room/platform_ops.html` | Removed deploy form; added disabled notice + historical log display |
| `control_room/help.py` | Updated Platform Ops guide — no git pull steps |
| `control_room/tests/test_deploy_security.py` | **New** — regression tests |
| `docs/ZRETA_DEPLOYMENT_PROCEDURE.md` | **New** — safe VPS deployment flow |
| `deploy/nginx/zreta.com.conf` | Added Phase 0 private-media deny rules (`/media/private/`, `/media/payments/proofs/`) |

### Preserved intentionally

- `PlatformOperationsSettings.last_deploy_*` fields — historical records unchanged
- `PlatformOpsView` URL — still serves email configuration
- `log_control_change()` — now records `deploy_blocked` when old action is attempted
- `git_remote` / `git_branch` model fields — no migration; legacy data only

---

## Deployment architecture (target)

```
Developer → git push → GitHub
                ↓
         SSH to VPS (operator)
                ↓
         git pull (known SHA)
                ↓
         deploy/scripts/deploy-app.sh
                ↓
         Gunicorn / systemd restart
                ↓
         /health/ check
```

Django HTTP layer does **not** participate in deployment.

---

## Tests added

`control_room/tests/test_deploy_security.py`:

1. `test_deploy_service_module_removed` — `control_room.services.deploy` cannot be imported
2. `test_platform_ops_page_does_not_offer_web_deploy` — no deploy form in HTML
3. `test_deploy_post_does_not_execute_subprocess` — POST `action=deploy` blocked; `subprocess.run` not called; audit log written
4. `test_no_subprocess_on_platform_ops_email_actions` — legitimate email save does not shell out

---

## Remaining risks

| Risk | Severity | Notes |
|------|----------|-------|
| Manual SSH deploy without CI | LOW | Operational; documented procedure |
| No automated GitHub Actions yet | LOW | Phase 1+ item |
| Historical deploy logs may reference old web deploy | INFO | Read-only display preserved |

Production Nginx (`deploy/nginx/zreta.com.conf`) now includes the same private-media deny blocks as `deploy/nginx/marketing-site.conf`. Operators must copy the updated config to the VPS and run `nginx -t` before reload on each deploy that changes Nginx files.

---

## Recommended production procedure

See **`docs/ZRETA_DEPLOYMENT_PROCEDURE.md`**.

---

## Verification checklist

- [x] `python manage.py test` — 102 tests pass
- [x] `python manage.py check` — no issues
- [x] `python manage.py makemigrations --check` — no pending migrations
- [x] Phase 0 commit `77fd427` files unchanged
- [x] `deploy/nginx/zreta.com.conf` — private-media deny rules aligned with Phase 0
- [ ] Stakeholder review before commit

---

## Stop condition

Phase 1A.1 implementation complete. **Do not commit until approved.** Phase 1A.2 not started.
