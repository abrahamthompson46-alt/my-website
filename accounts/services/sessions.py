from django.utils import timezone

from accounts.models import UserSession
from accounts.services.email import parse_user_agent


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def track_user_session(request, user):
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key
    if not session_key:
        return None

    user_agent = request.META.get("HTTP_USER_AGENT", "")
    UserSession.objects.filter(user=user, is_current=True).update(is_current=False)
    session, _ = UserSession.objects.update_or_create(
        session_key=session_key,
        defaults={
            "user": user,
            "ip_address": _client_ip(request),
            "user_agent": user_agent[:500],
            "device_label": parse_user_agent(user_agent),
            "last_seen_at": timezone.now(),
            "revoked_at": None,
            "is_current": True,
        },
    )
    return session


def touch_user_session(request):
    session_key = getattr(request.session, "session_key", None)
    if not session_key:
        return
    UserSession.objects.filter(session_key=session_key, revoked_at__isnull=True).update(
        last_seen_at=timezone.now()
    )


def get_active_sessions(user):
    return UserSession.objects.filter(user=user, revoked_at__isnull=True).order_by("-last_seen_at")


def revoke_session(user, session_id, current_session_key=None):
    session = UserSession.objects.filter(user=user, pk=session_id, revoked_at__isnull=True).first()
    if not session:
        return None
    session.revoked_at = timezone.now()
    session.is_current = False
    session.save(update_fields=["revoked_at", "is_current", "updated_at"])
    if current_session_key and session.session_key != current_session_key:
        from django.contrib.sessions.models import Session

        Session.objects.filter(session_key=session.session_key).delete()
    return session


def revoke_other_sessions(user, current_session_key):
    others = UserSession.objects.filter(user=user, revoked_at__isnull=True).exclude(
        session_key=current_session_key
    )
    keys = list(others.values_list("session_key", flat=True))
    if keys:
        from django.contrib.sessions.models import Session

        Session.objects.filter(session_key__in=keys).delete()
        others.update(revoked_at=timezone.now(), is_current=False)
