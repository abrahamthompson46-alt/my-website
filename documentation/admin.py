from django.contrib import admin

from documentation.models import DocAPIEndpoint, DocArticle, DocCategory, DocDownload, DocVideo


@admin.register(DocCategory)
class DocCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "product", "sort_order", "is_published")
    list_filter = ("is_published", "product")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(DocArticle)
class DocArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "article_type", "category", "product", "is_published", "is_featured", "sort_order")
    list_filter = ("article_type", "is_published", "is_featured", "category", "product")
    search_fields = ("title", "slug", "body", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "article_type", "category", "product", "version")}),
        ("Content", {"fields": ("excerpt", "body")}),
        ("Publishing", {"fields": ("is_published", "is_featured", "sort_order", "published_at")}),
    )


@admin.register(DocVideo)
class DocVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "product", "duration_minutes", "is_published", "sort_order")
    list_filter = ("is_published", "category", "product")
    search_fields = ("title", "description")


@admin.register(DocDownload)
class DocDownloadAdmin(admin.ModelAdmin):
    list_display = ("title", "file_type", "category", "product", "version", "is_published")
    list_filter = ("file_type", "is_published", "category", "product")
    search_fields = ("title", "description")


@admin.register(DocAPIEndpoint)
class DocAPIEndpointAdmin(admin.ModelAdmin):
    list_display = ("method", "path", "name", "category", "product", "is_published")
    list_filter = ("method", "is_published", "category", "product")
    search_fields = ("name", "path", "summary", "description")
