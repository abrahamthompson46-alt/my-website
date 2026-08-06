from django import template

from cms.services import get_section

register = template.Library()


@register.simple_tag
def cms_section(page_context, key):
    """Return section dict {section, items} for a given key."""
    data = get_section(page_context, key)
    if not data:
        return {"section": None, "items": []}
    return data


@register.filter
def get_item_extra(item, key):
    return (item.extra_data or {}).get(key, [])
