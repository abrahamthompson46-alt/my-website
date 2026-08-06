from accounts.models import AuditEventType, AuditLog


def log_audit_event(
    event_type,
    *,
    request=None,
    user=None,
    actor=None,
    message="",
    metadata=None,
    status_code=None,
):
    ip_address = None
    user_agent = ""
    request_path = ""
    request_method = ""

    if request is not None:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ip_address = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
        request_path = request.path[:255]
        request_method = request.method[:10]
        if user is None and getattr(request, "user", None) and request.user.is_authenticated:
            user = request.user

    return AuditLog.objects.create(
        event_type=event_type,
        user=user,
        actor=actor or user,
        ip_address=ip_address,
        user_agent=user_agent,
        request_path=request_path,
        request_method=request_method,
        status_code=status_code,
        message=message[:255],
        metadata=metadata or {},
    )
