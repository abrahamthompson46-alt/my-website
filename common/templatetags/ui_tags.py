from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()

BUTTON_VARIANTS = {"primary", "secondary", "tertiary", "destructive", "destructive-outline", "link", "ghost"}
BUTTON_SIZES = {"xs", "sm", "md", "lg", "xl"}
ALERT_VARIANTS = {"info", "success", "warning", "error"}
CARD_VARIANTS = {"default", "flat", "elevated", "interactive", "stat"}


def _resolve_url(url=None, url_name=None):
    if url:
        return url
    if url_name:
        try:
            return reverse(url_name)
        except NoReverseMatch:
            return "#"
    return "#"


@register.inclusion_tag("components/button.html")
def ui_button(
    label,
    url=None,
    url_name=None,
    variant="primary",
    size="md",
    icon=None,
    icon_position="leading",
    type="button",
    disabled=False,
    loading=False,
    full_width=False,
    extra_class="",
    aria_label=None,
    id=None,
    name=None,
    value=None,
    form=None,
    data_attrs=None,
):
    return {
        "label": label,
        "href": _resolve_url(url, url_name) if type == "link" else None,
        "variant": variant if variant in BUTTON_VARIANTS else "primary",
        "size": size if size in BUTTON_SIZES else "md",
        "icon": icon,
        "icon_position": icon_position,
        "type": type,
        "disabled": disabled,
        "loading": loading,
        "full_width": full_width,
        "extra_class": extra_class,
        "aria_label": aria_label or label,
        "id": id,
        "name": name,
        "value": value,
        "form": form,
        "data_attrs": data_attrs or {},
    }


@register.inclusion_tag("components/card.html")
def ui_card(
    title=None,
    subtitle=None,
    eyebrow=None,
    body="",
    footer="",
    variant="default",
    padding="md",
    href=None,
    url_name=None,
    extra_class="",
):
    return {
        "title": title,
        "subtitle": subtitle,
        "eyebrow": eyebrow,
        "body": body,
        "footer": footer,
        "variant": variant if variant in CARD_VARIANTS else "default",
        "padding": padding,
        "href": _resolve_url(href, url_name),
        "extra_class": extra_class,
    }


@register.inclusion_tag("components/alert.html")
def ui_alert(
    message,
    title=None,
    variant="info",
    dismissible=False,
    extra_class="",
):
    return {
        "title": title,
        "message": message,
        "variant": variant if variant in ALERT_VARIANTS else "info",
        "dismissible": dismissible,
        "extra_class": extra_class,
    }


@register.inclusion_tag("components/breadcrumbs.html")
def ui_breadcrumbs(items, extra_class=""):
    """
    items: list of dicts with 'label' and optional 'url' or 'url_name'
    Last item is treated as current page (no link).
    """
    resolved = []
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        resolved.append(
            {
                "label": item.get("label", ""),
                "url": None if is_last else _resolve_url(item.get("url"), item.get("url_name")),
                "is_current": is_last,
            }
        )
    return {"items": resolved, "extra_class": extra_class}


@register.inclusion_tag("components/search/search_bar.html")
def ui_search(
    action="",
    placeholder="Search…",
    name="q",
    value="",
    size="md",
    variant="inline",
    extra_class="",
):
    return {
        "action": action,
        "placeholder": placeholder,
        "name": name,
        "value": value,
        "size": size,
        "variant": variant,
        "extra_class": extra_class,
    }


@register.inclusion_tag("components/theme_switcher.html")
def ui_theme_switcher(variant="segmented", extra_class=""):
    return {"variant": variant, "extra_class": extra_class}


@register.inclusion_tag("components/flash_messages.html")
def ui_flash_messages(messages=None):
    return {"messages": messages}


@register.inclusion_tag("components/forms/field.html")
def ui_field(
    field,
    label=None,
    help_text=None,
    required_indicator=True,
    show_optional=False,
    show_label=True,
    extra_class="",
):
    if label is None:
        display_label = field.label if show_label else None
    elif show_label:
        display_label = label
    else:
        display_label = None

    return {
        "field": field,
        "label": display_label,
        "help_text": help_text if help_text is not None else getattr(field, "help_text", ""),
        "required_indicator": required_indicator,
        "show_optional": show_optional,
        "extra_class": extra_class,
        "errors": field.errors if hasattr(field, "errors") else [],
    }


@register.inclusion_tag("components/table/table.html")
def ui_table(
    columns,
    rows=None,
    variant="default",
    compact=False,
    striped=False,
    selectable=False,
    empty_message="No data available.",
    empty_action_label=None,
    empty_action_url=None,
    empty_action_url_name=None,
    extra_class="",
):
    """
    columns: list of dicts — label, key, sortable (bool), align (left|center|right)
    rows: list of dicts — keys match column keys; optional 'actions' list
    """
    return {
        "columns": columns,
        "rows": rows or [],
        "variant": variant,
        "compact": compact,
        "striped": striped,
        "selectable": selectable,
        "empty_message": empty_message,
        "empty_action_label": empty_action_label,
        "empty_action_url": _resolve_url(empty_action_url, empty_action_url_name),
        "empty_action_url_name": empty_action_url_name,
        "extra_class": extra_class,
    }


@register.inclusion_tag("components/modal/modal.html")
def ui_modal(
    id,
    title,
    size="md",
    dismissible=True,
    body="",
    footer_actions=None,
    extra_class="",
):
    return {
        "modal_id": id,
        "title": title,
        "size": size,
        "dismissible": dismissible,
        "body": body,
        "footer_actions": footer_actions or [],
        "extra_class": extra_class,
    }


@register.inclusion_tag("components/badge.html")
def ui_badge(label, variant="default", size="sm", extra_class=""):
    return {
        "label": label,
        "variant": variant,
        "size": size,
        "extra_class": extra_class,
    }


@register.inclusion_tag("components/forms/form_fields.html")
def ui_form_fields(form):
    return {"form": form}


@register.filter
def get_item(mapping, key):
    if mapping is None:
        return "—"
    if isinstance(mapping, dict):
        if key not in mapping or mapping[key] is None or mapping[key] == "":
            return "—"
        return mapping[key]
    value = getattr(mapping, key, None)
    return value if value not in (None, "") else "—"


@register.simple_tag
def ui_icon(name, size="md", extra_class=""):
    return f'<svg class="icon icon--{size} {extra_class}" aria-hidden="true" data-icon="{name}"></svg>'
