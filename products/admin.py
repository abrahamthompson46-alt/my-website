from django.contrib import admin

from cms.models import ProductContentSection
from products.models import (
    ComparisonAttribute,
    PlanFeature,
    PricingPlan,
    PricingTier,
    Product,
    ProductCategory,
    ProductComparisonEntry,
    ProductDemoRequest,
    ProductDownload,
    ProductFeature,
    ProductModule,
    ProductScreenshot,
    ProductVideo,
)


class ProductModuleInline(admin.TabularInline):
    model = ProductModule
    extra = 0
    prepopulated_fields = {"slug": ("name",)}


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 0
    filter_horizontal = ["plans"]


class PricingTierInline(admin.TabularInline):
    model = PricingTier
    extra = 0


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 0


class PricingPlanInline(admin.StackedInline):
    model = PricingPlan
    extra = 0
    prepopulated_fields = {"slug": ("name",)}
    show_change_link = True


class ProductScreenshotInline(admin.TabularInline):
    model = ProductScreenshot
    extra = 0
    fields = ("title", "alt_text", "kind", "image", "caption", "sort_order", "is_featured")


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 0


class ProductDownloadInline(admin.TabularInline):
    model = ProductDownload
    extra = 0


class ProductContentSectionInline(admin.StackedInline):
    model = ProductContentSection
    extra = 0


class ProductComparisonEntryInline(admin.TabularInline):
    model = ProductComparisonEntry
    extra = 0


@admin.register(ProductScreenshot)
class ProductScreenshotAdmin(admin.ModelAdmin):
    list_display = ("title", "alt_text", "product", "kind", "sort_order", "is_featured")
    list_filter = ("product", "kind", "is_featured")
    search_fields = ("title", "alt_text", "product__name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)


@admin.register(ProductVideo)
class ProductVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "video_type", "sort_order")
    list_filter = ("product", "video_type")
    search_fields = ("title", "product__name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)


@admin.register(ProductDownload)
class ProductDownloadAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "file_type", "sort_order")
    list_filter = ("product", "file_type")
    search_fields = ("title", "product__name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "status", "is_featured", "is_published", "sort_order")
    list_filter = ("status", "is_featured", "is_published", "category", "accent")
    search_fields = ("name", "slug", "tagline")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        ProductModuleInline,
        ProductFeatureInline,
        PricingPlanInline,
        ProductScreenshotInline,
        ProductVideoInline,
        ProductDownloadInline,
        ProductContentSectionInline,
        ProductComparisonEntryInline,
    ]
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "tagline", "status", "accent")}),
        ("Descriptions", {"fields": ("short_description", "long_description")}),
        ("Publishing", {"fields": ("is_featured", "is_published", "sort_order", "launch_date")}),
        ("Links", {"fields": ("demo_url", "register_url", "external_app_url", "documentation_url", "hero_image")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "billing_interval", "is_popular", "is_contact_sales", "is_published")
    list_filter = ("billing_interval", "is_popular", "is_contact_sales", "is_published", "product")
    search_fields = ("name", "product__name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [PricingTierInline, PlanFeatureInline]


@admin.register(ComparisonAttribute)
class ComparisonAttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "value_type", "sort_order", "is_active")
    list_filter = ("value_type", "is_active", "group")
    search_fields = ("name", "slug", "group")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductDemoRequest)
class ProductDemoRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "work_email", "company", "product", "status", "created_at")
    list_filter = ("status", "product", "created_at")
    search_fields = ("full_name", "work_email", "company")
    readonly_fields = ("created_at", "updated_at")
