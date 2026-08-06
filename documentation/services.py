"""Documentation search and query helpers."""

from django.db.models import Q

from documentation.constants import SECTIONS
from documentation.models import DocAPIEndpoint, DocArticle, DocCategory, DocDownload, DocVideo


def get_published_categories(product=None):
    qs = DocCategory.objects.filter(is_published=True)
    if product:
        qs = qs.filter(Q(product=product) | Q(product__isnull=True))
    return qs.order_by("sort_order", "name")


def get_articles(article_type=None, product=None, featured_only=False):
    qs = DocArticle.objects.filter(is_published=True).select_related("category", "product")
    if article_type:
        qs = qs.filter(article_type=article_type)
    if product:
        qs = qs.filter(Q(product=product) | Q(product__isnull=True))
    if featured_only:
        qs = qs.filter(is_featured=True)
    return qs.order_by("sort_order", "title")


def get_videos(product=None):
    qs = DocVideo.objects.filter(is_published=True).select_related("category", "product")
    if product:
        qs = qs.filter(Q(product=product) | Q(product__isnull=True))
    return qs.order_by("sort_order", "title")


def get_downloads(product=None):
    qs = DocDownload.objects.filter(is_published=True).select_related("category", "product")
    if product:
        qs = qs.filter(Q(product=product) | Q(product__isnull=True))
    return qs.order_by("sort_order", "title")


def get_api_endpoints(product=None):
    qs = DocAPIEndpoint.objects.filter(is_published=True).select_related("category", "product")
    if product:
        qs = qs.filter(Q(product=product) | Q(product__isnull=True))
    return qs.order_by("sort_order", "path")


def get_section_by_slug(slug):
    for section in SECTIONS:
        if section["slug"] == slug:
            return section
    return None


def search_documentation(query, product=None):
    if not query or len(query.strip()) < 2:
        return {"articles": [], "videos": [], "downloads": [], "api_endpoints": [], "categories": []}

    q = query.strip()
    article_qs = DocArticle.objects.filter(is_published=True).filter(
        Q(title__icontains=q) | Q(body__icontains=q) | Q(excerpt__icontains=q)
    )
    video_qs = DocVideo.objects.filter(is_published=True).filter(
        Q(title__icontains=q) | Q(description__icontains=q)
    )
    download_qs = DocDownload.objects.filter(is_published=True).filter(
        Q(title__icontains=q) | Q(description__icontains=q)
    )
    api_qs = DocAPIEndpoint.objects.filter(is_published=True).filter(
        Q(name__icontains=q) | Q(path__icontains=q) | Q(summary__icontains=q) | Q(description__icontains=q)
    )
    category_qs = DocCategory.objects.filter(is_published=True).filter(
        Q(name__icontains=q) | Q(description__icontains=q)
    )

    if product:
        scope = Q(product=product) | Q(product__isnull=True)
        article_qs = article_qs.filter(scope)
        video_qs = video_qs.filter(scope)
        download_qs = download_qs.filter(scope)
        api_qs = api_qs.filter(scope)
        category_qs = category_qs.filter(scope)

    return {
        "articles": article_qs.select_related("category")[:20],
        "videos": video_qs.select_related("category")[:10],
        "downloads": download_qs.select_related("category")[:10],
        "api_endpoints": api_qs.select_related("category")[:15],
        "categories": category_qs[:10],
    }


def resolve_product(slug):
    if not slug:
        return None
    from products.models import Product

    return Product.objects.filter(slug=slug, is_published=True).first()
