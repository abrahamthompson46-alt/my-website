from django import template

from products.services.trial_links import get_product_demo_url, get_product_trial_url
from products.services.availability import is_purchasable

register = template.Library()


@register.simple_tag
def product_trial_url(product):
    return get_product_trial_url(product)


@register.simple_tag
def product_demo_url(product):
    return get_product_demo_url(product)


@register.filter
def product_purchasable(product):
    return is_purchasable(product)
