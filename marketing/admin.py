from django.contrib import admin

from marketing.models import (
    Author,
    BlogCategory,
    BlogPost,
    BlogTag,
    CaseStudy,
    MarketingEvent,
    MarketingResource,
    NewsletterSubscriber,
    SuccessStory,
    WhitePaper,
)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "slug", "role", "is_published")
    search_fields = ("full_name", "role", "bio")
    prepopulated_fields = {"slug": ("full_name",)}


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "is_published", "is_featured", "published_at")
    list_filter = ("is_published", "is_featured", "category", "tags")
    search_fields = ("title", "slug", "body", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    date_hierarchy = "published_at"
    fieldsets = (
        (None, {"fields": ("title", "slug", "category", "author", "author_name", "tags")}),
        ("Content", {"fields": ("excerpt", "body", "featured_image", "read_time_minutes")}),
        ("Publishing", {"fields": ("is_published", "is_featured", "published_at")}),
        ("SEO", {"fields": ("meta_title", "meta_description", "og_image"), "classes": ("collapse",)}),
    )


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "source", "is_active", "created_at")
    list_filter = ("is_active", "source")
    search_fields = ("email", "full_name")


@admin.register(MarketingEvent)
class MarketingEventAdmin(admin.ModelAdmin):
    list_display = ("title", "event_type", "starts_at", "is_featured", "is_published")
    list_filter = ("event_type", "is_published", "is_featured")
    search_fields = ("title", "location")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "starts_at"


@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "industry", "is_featured", "is_published")
    list_filter = ("is_published", "is_featured", "product")
    search_fields = ("title", "company", "quote")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ("title", "client_name", "industry", "is_featured", "is_published")
    list_filter = ("is_published", "is_featured", "product")
    search_fields = ("title", "client_name")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(WhitePaper)
class WhitePaperAdmin(admin.ModelAdmin):
    list_display = ("title", "is_gated", "is_featured", "is_published", "product")
    list_filter = ("is_published", "is_gated", "is_featured", "product")
    search_fields = ("title", "excerpt")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(MarketingResource)
class MarketingResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "resource_type", "is_featured", "is_published", "product")
    list_filter = ("resource_type", "is_published", "is_featured")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
