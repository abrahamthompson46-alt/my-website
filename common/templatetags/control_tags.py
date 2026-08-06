from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def feature_enabled(context, key):
    flags = context.get("FEATURE_FLAGS", {})
    return flags.get(key, True)


@register.filter
def admin_changelist_url(admin_model):
    if not admin_model or "." not in admin_model:
        return "/admin/"
    app_label, model_name = admin_model.split(".", 1)
    return f"/admin/{app_label}/{model_name}/"
