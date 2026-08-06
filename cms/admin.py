from django.contrib import admin

from cms.models import (
    CMSDownload,
    CMSPage,
    FAQ,
    FAQCategory,
    HeroBanner,
    NewsArticle,
    PageSection,
    ProductContentSection,
    SectionItem,
    TeamMember,
    Testimonial,
)


class SectionItemInline(admin.TabularInline):
    model = SectionItem
    extra = 1
    fields = ("title", "subtitle", "description", "icon", "value", "sort_order", "is_active")


class PageSectionInline(admin.StackedInline):
    model = PageSection
    extra = 0
    show_change_link = True
    fields = ("section_key", "eyebrow", "title", "subtitle", "body", "is_active", "sort_order", "settings")


@admin.register(CMSPage)
class CMSPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "page_type", "is_published", "updated_at")
    list_filter = ("page_type", "is_published")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PageSectionInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "page_type", "hero", "is_published", "published_at")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )


@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
    list_display = ("page", "section_key", "title", "is_active", "sort_order")
    list_filter = ("page", "is_active")
    search_fields = ("section_key", "title", "page__title")
    inlines = [SectionItemInline]


@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ("name", "placement", "headline", "is_active")
    list_filter = ("placement", "is_active")
    search_fields = ("name", "headline")


@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "product", "is_published", "sort_order")
    list_filter = ("is_published", "category", "product")
    search_fields = ("question", "answer")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("author_name", "company", "is_featured", "show_on_home", "is_published", "sort_order")
    list_filter = ("is_published", "is_featured", "show_on_home", "product")
    search_fields = ("author_name", "company", "quote")


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role", "department", "is_leadership", "show_on_about", "is_published")
    list_filter = ("is_leadership", "show_on_about", "is_published", "department")
    search_fields = ("full_name", "role")


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "is_featured", "published_at")
    list_filter = ("is_published", "is_featured", "category")
    search_fields = ("title", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"


@admin.register(CMSDownload)
class CMSDownloadAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "product", "is_published", "sort_order")
    list_filter = ("category", "is_published", "product")
    search_fields = ("title",)


@admin.register(ProductContentSection)
class ProductContentSectionAdmin(admin.ModelAdmin):
    list_display = ("product", "title", "sort_order", "is_published")
    list_filter = ("is_published", "product")
    search_fields = ("title", "product__name")
