"""Product availability helpers shared by catalog UI and checkout."""

from products.models import ProductStatus

# Statuses customers can purchase or start a trial for.
PURCHASABLE_STATUSES = frozenset({ProductStatus.GA, ProductStatus.BETA})


def is_purchasable(product) -> bool:
    return bool(
        product
        and product.is_published
        and product.status in PURCHASABLE_STATUSES
    )
