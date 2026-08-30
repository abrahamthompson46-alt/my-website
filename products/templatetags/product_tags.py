from django import template

from products.services.trial_links import get_product_trial_url

register = template.Library()


@register.simple_tag
def product_trial_url(product):
    return get_product_trial_url(product)
