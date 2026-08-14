# Production Hardening Implementation Report

**Date:** 2026-08-13  
**Baseline:** `docs/PRODUCTION_HARDENING_AUDIT.md`  
**Production URL:** https://www.zreta.com  

This report documents repository changes made to harden the Zreta marketing site. **It does not claim the site is fully secure.** Residual risks are listed honestly at the end.

---

## Summary

| Priority | Status | Outcome |
|----------|--------|---------|
| 1 — Invitation auth boundary | Done | Existing users no longer receive authenticated sessions from token alone |
| 2 — MFA rescan hardening | Done | Login challenge cannot re-enroll TOTP via `?rescan=1` |
| 3 — RBAC hardening | Done | High-risk control room / ops actions require platform owner/admin roles |
| 4 — Deployment consistency | Done | Repo systemd/gunicorn/deploy guard aligned to live `:8001` / `marketing-runtime` |
| 5 — Nginx hardening | Done (repo) | Static/media, private-media deny, sensitive-path blocks documented in repo configs |
| 6 — Backup / DR | Done (docs) | `docs/BACKUP_AND_DISASTER_RECOVERY.md` + existing drill scripts referenced |
| 7 — Obsolete deployment material | Documented | Legacy `venv/` identified; not deleted |

**Tests:** 133 passing (21 new security regression tests).  
**Checks:** `python manage.py check` — pass. `python manage.py check --deploy` — pass with expected dev-environment SSL/SECRET_KEY warnings.

**Not performed in this pass:** Live VPS nginx/systemd changes, live restore drill execution, legacy `venv/` deletion.

---

## Priority 1 — Invitation authentication fix

### Problem
An existing user accepting a staff invitation was logged in via `auth_login()` without password or MFA, bypassing the normal authentication boundary.

### Solution
- **Existing users (unauthenticated):** `accept_invitation()` runs, then redirect to login with `?next=` — **no session created**
- **Existing users (authenticated as matching account):** accept in place, remain authenticated
- **New users:** unchanged — account creation + login for onboarding/MFA enrollment
- **Middleware:** `/accounts/invite/` added to MFA-exempt prefixes so authenticated staff can complete acceptance before MFA enforcement redirects

### Files changed
- `accounts/views.py` — `AcceptInvitationView.post()`
- `accounts/middleware.py` — MFA exempt prefix for invite path
- `templates/accounts/accept_invite.html` — UX copy for existing users

### Tests added
- `accounts/tests/test_invitation_security.py` (6 tests)

### Security impact
Invitation possession no longer equals authenticated identity for existing accounts.

---

## Priority 2 — MFA rescan hardening

### Problem
During the login MFA challenge, `?rescan=1` could start re-enrollment and replace the enrolled authenticator without completing normal MFA.

### Solution
- `MFAVerifyView` GET with `rescan=1`: clears stale session secret, shows warning, presents normal verify form only
- POST: removed path that accepted `mfa_rescan_secret` to replace TOTP during login
- Authenticated re-enrollment remains on `MFAEnrollView` (portal, after login)

### Files changed
- `accounts/views.py` — `MFAVerifyView`
- `templates/accounts/mfa_verify.html` — removed rescan UI
- `accounts/tests/test_mfa.py` — rescan blocked during challenge tests

### Security impact
URL parameters cannot weaken the login MFA state machine.

---

## Priority 3 — RBAC hardening

### Problem
Destructive/configuration views relied primarily on `is_staff`, granting broad access to all staff users.

### Solution
Used existing RBAC roles (`platform-owner`, `platform-admin`):

| Mixin | Permission helper | Applied to |
|-------|-------------------|------------|
| `PlatformSettingsMixin` | `user_can_manage_platform_settings()` | Settings, navigation, redirects, announcements, flags, product/doc CRUD, brand zip |
| `PlatformOwnerMixin` | `user_can_manage_platform_ops()` | Seed runs, platform ops |
| `TeamManagementMixin` | `user_can_manage_team()` | Team views (pre-existing) |
| `OpsActionsMixin` | `user_can_manage_operations_actions()` | Demo/ticket/payment POST actions |

Read-only views (dashboard, content hub, changelog, setup page, product/doc lists, brand kit download) remain `ControlRoomMixin` (staff read access).

### Files changed
- `accounts/services/rbac.py` — `user_can_manage_platform_settings()`, `user_can_manage_operations_actions()`
- `control_room/mixins.py` — `PlatformSettingsMixin`
- `control_room/views.py` — mixin assignments
- `control_room/product_views.py` — write views → `PlatformSettingsMixin`
- `control_room/doc_views.py` — write views → `PlatformSettingsMixin`
- `operations/mixins.py` — `OpsActionsMixin`
- `operations/action_views.py` — ops POST views

### Tests added
- `control_room/tests/test_rbac_hardening.py` (9 tests)
- `operations/tests/test_rbac_actions.py` (5 tests)
- `control_room/tests/test_views.py` — test user assigned `platform-admin` role

### Security impact
Least-privilege enforcement on high-risk operations; generic staff retain read-only operational visibility.

---

## Priority 4 — Deployment configuration consistency

### Problem
Repository artifacts described Unix socket / `www-data` while live production uses `127.0.0.1:8001` / `marketing-runtime` / `.venv`.

### Solution (repository only — no live migration)

| Setting | Canonical value |
|---------|-----------------|
| Service user | `marketing` |
| Service group | `marketing-runtime` |
| Virtualenv | `/var/www/marketing-site/.venv` |
| Gunicorn bind | `127.0.0.1:8001` |
| Workers | 3 (default in gunicorn.conf.py) |
| Django settings | `config.settings.production` (via `.env`) |
| Environment file | `/var/www/marketing-site/.env` (mode 640, group `marketing-runtime`) |
| Dependencies | PostgreSQL, Redis |

### Files changed
- `deploy/systemd/marketing-site.service` — `Group=marketing-runtime`
- `deploy/gunicorn/gunicorn.conf.py` — default bind `127.0.0.1:8001`, group `marketing-runtime`, 3 workers
- `deploy/scripts/deploy-app.sh` — guard blocks obsolete socket/`www-data`/`churchhub` layouts; health check via `:8001`

---

## Priority 5 — Nginx hardening (repository configs)

### Problem
Live nginx was a minimal proxy without static/media aliases or private-media deny blocks. Repo configs referenced Unix sockets.

### Solution
Updated repository nginx configs (for deliberate operator install on VPS):

- Upstream: `127.0.0.1:8001`
- `/static/` → `staticfiles/`
- `/media/` → `media/` with `^~ /media/private/` and `^~ /media/payments/proofs/` deny
- Sensitive path deny blocks (`.env`, `.git`, `.venv`, `venv`, logs, deploy, cert/key extensions)
- Security headers: X-Frame-Options, X-Content-Type-Options, Referrer-Policy (compatible with Django middleware)

### Files changed
- `deploy/nginx/zreta.com-marketing.conf`
- `deploy/nginx/marketing-site.conf`
- `deploy/nginx/zreta.com.conf`

**Live production nginx was not modified in this pass.** Apply configs during a planned maintenance window:

```bash
sudo cp deploy/nginx/zreta.com-marketing.conf /etc/nginx/sites-available/zreta.com
sudo nginx -t && sudo systemctl reload nginx
```

---

## Priority 6 — Backup and recovery

### Deliverable
- `docs/BACKUP_AND_DISASTER_RECOVERY.md` — backup scope, schedule, retention, verify/restore/drill procedures, off-site recommendations

### Existing infrastructure (unchanged)
- `deploy/scripts/backup-all.sh`, `test-restore-drill.sh`, systemd timer
- Backup root: `/var/backups/zreta`
- Log: `/var/log/zreta-backup`

### Recommended next operator action
Run monthly: `sudo bash deploy/scripts/test-restore-drill.sh` and record results.

---

## Priority 7 — Obsolete deployment material

### Legacy virtualenv on production VPS
- **Path:** `/var/www/marketing-site/venv` (legacy, `churchhub:churchhub` ownership reported in audit)
- **Active:** `/var/www/marketing-site/.venv`
- **Repository references:** none active in systemd/gunicorn/deploy-app.sh after this pass
- **Action:** Do **not** delete until operator confirms no cron/scripts reference `venv/`. Removal is a separate maintenance task.

### Repository obsolete references updated
- Socket-based upstream defaults removed from canonical nginx/gunicorn configs
- `deploy-app.sh` guard inverted to protect `:8001` layout

### Not removed
- Phase migration scripts (`phase1-*`, `phase3-*`) — historical ChurchHub migration artifacts, still referenced in docs
- `deploy/scripts/fix-churchhub-env.sh` — ChurchHub-specific, unrelated to marketing runtime

---

## Tests executed

```bash
python manage.py check
python manage.py check --deploy
python manage.py test
```

| Suite | Count |
|-------|-------|
| Full suite | 133 OK |
| New security tests | 21 |
| Prior baseline | 112 |

New test modules:
- `accounts/tests/test_invitation_security.py`
- `control_room/tests/test_rbac_hardening.py`
- `operations/tests/test_rbac_actions.py`

Updated: `accounts/tests/test_mfa.py`, `control_room/tests/test_views.py`

---

## Acceptance criteria checklist

| Criterion | Status |
|-----------|--------|
| Invitation tokens cannot bypass auth/MFA for existing users | Done (code + tests) |
| MFA rescan cannot bypass enrolled MFA at login | Done (code + tests) |
| High-risk operations use RBAC | Done (code + tests) |
| Repo deployment matches live architecture | Done (repo artifacts) |
| Nginx safely serves/proxies required resources | Done (repo configs; live apply pending) |
| Private media not accidentally exposed via nginx | Done (repo deny blocks; live apply pending) |
| Sensitive files blocked at nginx layer | Done (repo configs; live apply pending) |
| Backup restore procedure documented | Done |
| Legacy deployment references identified | Done |
| No unnecessary architecture changes | Done |
| Existing + new tests pass | 133/133 |
| `manage.py check` passes | Yes |
| Production health/homepage/login 200 | Not re-verified live in this pass (read-only assumed healthy) |

---

## Remaining risks (honest)

1. **Live nginx unchanged** — production still proxies everything to Gunicorn without repo hardening until operator applies config.
2. **Live vs repo systemd group** — if live unit differs from repo, `deploy-app.sh` may overwrite; verify before next deploy.
3. **Legacy `venv/` on disk** — consumes space; confusion risk if referenced manually.
4. **Off-site backups** — not automated; VPS disk failure would lose local backups.
5. **Restore drill** — documented but not executed in this implementation pass.
6. **Rate-limit IP trust** — `X-Forwarded-For` trust boundary depends on nginx setting real IP (audit finding).
7. **Django admin** — still available at `/admin/` for superusers; not part of RBAC hardening scope.
8. **Dev `check --deploy` warnings** — SECRET_KEY/HSTS/SSL cookie warnings expected in local dev; production `.env` should satisfy these (verify on VPS).
9. **Authenticated invite acceptance** — user must already be logged in as the invited account; no password re-verification at accept time (acceptable trade-off for UX; role alone does not grant ops access without login for unauthenticated path).

---

## Recommended next steps

1. Apply `deploy/nginx/zreta.com-marketing.conf` on production during maintenance; verify `/health/`, static, public media, blocked private media.
2. Confirm systemd unit on VPS matches repo (`Group=marketing-runtime`, gunicorn via `.venv` + config file).
3. Run `sudo bash deploy/scripts/test-restore-drill.sh` and log outcome.
4. Configure off-site backup sync for `/var/backups/zreta/`.
5. After dependency audit on VPS, remove `/var/www/marketing-site/venv`.
6. Commit changes in logical groups (invitation → MFA → RBAC → deploy → nginx → docs).

---

## Files changed (complete list)

**Application security**
- `accounts/views.py`
- `accounts/middleware.py`
- `accounts/services/rbac.py`
- `templates/accounts/accept_invite.html`
- `templates/accounts/mfa_verify.html`
- `control_room/mixins.py`
- `control_room/views.py`
- `control_room/product_views.py`
- `control_room/doc_views.py`
- `operations/mixins.py`
- `operations/action_views.py`

**Tests**
- `accounts/tests/test_invitation_security.py` (new)
- `accounts/tests/test_mfa.py`
- `control_room/tests/test_rbac_hardening.py` (new)
- `control_room/tests/test_views.py`
- `operations/tests/test_rbac_actions.py` (new)

**Deployment / infra (repo only)**
- `deploy/systemd/marketing-site.service`
- `deploy/gunicorn/gunicorn.conf.py`
- `deploy/scripts/deploy-app.sh`
- `deploy/nginx/zreta.com-marketing.conf`
- `deploy/nginx/marketing-site.conf`
- `deploy/nginx/zreta.com.conf`

**Documentation**
- `docs/BACKUP_AND_DISASTER_RECOVERY.md` (new)
- `docs/PRODUCTION_HARDENING_IMPLEMENTATION.md` (this file)
