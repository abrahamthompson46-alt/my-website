"""Product availability helpers shared by catalog UI and checkout."""

from products.models import ProductStatus

# Statuses customers can purchase or start a trial for.
PURCHASABLE_STATUSES = frozenset({ProductStatus.GA, ProductStatus.BETA})


def is_purchasable(product) -> bool:
    """Published products in GA or Beta can be trialed or bought."""
    return bool(
        product
        and getattr(product, "is_published", False)
        and getattr(product, "status", None) in PURCHASABLE_STATUSES
    )
