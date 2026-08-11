from django import forms

from common.forms import BaseModelForm
from control_room.models import FeatureFlag, NavigationMenu, PlatformSettings, RedirectRule, SiteAnnouncement
from control_room.services.theme import HEX_PATTERN, THEME_PRESETS, get_preset_choices, normalize_hex
from control_room.validators import BRAND_FILE_EXTENSIONS, validate_brand_file_size
from products.models import Product, ProductCategory
from products.models.pricing import PlanFeature, PricingPlan, PricingTier


class PlatformSettingsForm(forms.ModelForm):
    class Meta:
        model = PlatformSettings
        fields = [
            "site_name",
            "site_tagline",
            "site_description",
            "brand_theme_preset",
            "brand_primary_color",
            "brand_accent_color",
            "brand_logo",
            "brand_favicon",
            "default_seo_title",
            "seo_twitter_handle",
            "seo_default_og_image",
            "contact_email",
            "support_email",
            "contact_phone",
            "footer_copyright",
            "header_cta_primary_label",
            "header_cta_primary_url_name",
            "header_cta_secondary_label",
            "header_cta_secondary_url_name",
            "maintenance_mode",
            "maintenance_message",
            "demo_form_enabled",
            "newsletter_enabled",
            "partner_program_enabled",
            "public_registration_enabled",
            "social_linkedin_url",
            "social_twitter_url",
            "social_youtube_url",
            "support_sla_hours",
        ]
        widgets = {
            "site_description": forms.Textarea(attrs={"rows": 3}),
            "maintenance_message": forms.Textarea(attrs={"rows": 3}),
            "brand_primary_color": forms.TextInput(attrs={"type": "color", "class": "control-color-input"}),
            "brand_accent_color": forms.TextInput(attrs={"type": "color", "class": "control-color-input"}),
            "brand_logo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ",".join(f".{ext}" for ext in BRAND_FILE_EXTENSIONS),
                }
            ),
            "brand_favicon": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ",".join(f".{ext}" for ext in BRAND_FILE_EXTENSIONS),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["brand_theme_preset"].widget = forms.Select(
            choices=get_preset_choices(),
            attrs={"class": "form-select", "data-brand-preset-select": ""},
        )
        self.fields["brand_primary_color"].widget.attrs["data-brand-primary"] = ""
        self.fields["brand_accent_color"].widget.attrs["data-brand-accent"] = ""

    def clean(self):
        cleaned = super().clean()
        preset = cleaned.get("brand_theme_preset") or "zreta_indigo"
        if preset != "custom" and preset in THEME_PRESETS:
            cleaned["brand_primary_color"] = THEME_PRESETS[preset]["primary"]
            cleaned["brand_accent_color"] = THEME_PRESETS[preset]["accent"]
        else:
            primary = normalize_hex(cleaned.get("brand_primary_color", ""), THEME_PRESETS["zreta_indigo"]["primary"])
            accent = normalize_hex(cleaned.get("brand_accent_color", ""), THEME_PRESETS["zreta_indigo"]["accent"])
            cleaned["brand_primary_color"] = primary
            cleaned["brand_accent_color"] = accent
        return cleaned

    def clean_brand_primary_color(self):
        value = self.cleaned_data.get("brand_primary_color", "")
        if value and not HEX_PATTERN.match(value.strip()):
            raise forms.ValidationError("Enter a valid hex color, e.g. #1e3a5f")
        return value

    def clean_brand_accent_color(self):
        value = self.cleaned_data.get("brand_accent_color", "")
        if value and not HEX_PATTERN.match(value.strip()):
            raise forms.ValidationError("Enter a valid hex color, e.g. #c9a227")
        return value

    def _clean_brand_upload(self, field_name: str):
        upload = self.cleaned_data.get(field_name)
        if upload:
            validate_brand_file_size(upload)
        return upload

    def clean_brand_logo(self):
        return self._clean_brand_upload("brand_logo")

    def clean_brand_favicon(self):
        return self._clean_brand_upload("brand_favicon")


class NavigationMenuForm(forms.ModelForm):
    structure_json = forms.CharField(
        label="Navigation structure (JSON)",
        widget=forms.Textarea(attrs={"rows": 18, "class": "control-code-input"}),
        help_text="Edit menu links and sections. Save to apply site-wide without code changes.",
    )

    class Meta:
        model = NavigationMenu
        fields = ["name", "is_active"]

    def __init__(self, *args, **kwargs):
        import json

        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["structure_json"].initial = json.dumps(self.instance.structure, indent=2)

    def clean_structure_json(self):
        import json

        raw = self.cleaned_data.get("structure_json", "[]")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid JSON: {exc}") from exc
        if not isinstance(data, list):
            raise forms.ValidationError("Navigation structure must be a JSON array.")
        return data

    def save(self, commit=True):
        self.instance.structure = self.cleaned_data["structure_json"]
        return super().save(commit=commit)


class RedirectRuleForm(forms.ModelForm):
    class Meta:
        model = RedirectRule
        fields = ["from_path", "to_path", "to_url_name", "redirect_type", "is_active", "notes"]


class SiteAnnouncementForm(forms.ModelForm):
    class Meta:
        model = SiteAnnouncement
        fields = [
            "title",
            "message",
            "variant",
            "link_url",
            "link_label",
            "starts_at",
            "ends_at",
            "show_on_public",
            "show_on_portal",
            "is_active",
            "sort_order",
        ]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 3}),
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class FeatureFlagForm(forms.ModelForm):
    class Meta:
        model = FeatureFlag
        fields = ["key", "label", "description", "is_enabled"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class ProductForm(BaseModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "tagline",
            "short_description",
            "long_description",
            "status",
            "accent",
            "is_featured",
            "is_published",
            "sort_order",
            "launch_date",
            "external_app_url",
            "demo_url",
            "register_url",
            "documentation_url",
            "hero_image",
            "meta_title",
            "meta_description",
        ]
        widgets = {
            "short_description": forms.Textarea(attrs={"rows": 2}),
            "long_description": forms.Textarea(attrs={"rows": 4}),
            "meta_description": forms.Textarea(attrs={"rows": 2}),
            "launch_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = ProductCategory.objects.filter(is_active=True).order_by("sort_order")
        self.fields["slug"].help_text = "URL-friendly identifier (auto-generated from name if left blank)."


class PricingPlanForm(BaseModelForm):
    class Meta:
        model = PricingPlan
        fields = [
            "name",
            "slug",
            "description",
            "billing_interval",
            "is_popular",
            "is_contact_sales",
            "is_published",
            "sort_order",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class PricingTierForm(BaseModelForm):
    class Meta:
        model = PricingTier
        fields = ["region", "currency", "amount", "price_label"]


class PlanFeatureForm(BaseModelForm):
    class Meta:
        model = PlanFeature
        fields = ["text", "is_included", "sort_order"]


class DocCategoryForm(BaseModelForm):
    class Meta:
        from documentation.models import DocCategory

        model = DocCategory
        fields = ["name", "slug", "description", "icon", "product", "sort_order", "is_published"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.order_by("sort_order", "name")
        self.fields["slug"].required = False


class DocArticleForm(BaseModelForm):
    class Meta:
        from documentation.models import DocArticle

        model = DocArticle
        fields = [
            "title",
            "slug",
            "article_type",
            "category",
            "product",
            "excerpt",
            "body",
            "version",
            "is_published",
            "is_featured",
            "sort_order",
        ]
        widgets = {
            "excerpt": forms.Textarea(attrs={"rows": 2}),
            "body": forms.Textarea(attrs={"rows": 14}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from documentation.models import DocCategory

        self.fields["category"].queryset = DocCategory.objects.order_by("sort_order", "name")
        self.fields["product"].queryset = Product.objects.order_by("sort_order", "name")
        self.fields["slug"].required = False


class DocVideoForm(BaseModelForm):
    class Meta:
        from documentation.models import DocVideo

        model = DocVideo
        fields = [
            "title",
            "description",
            "category",
            "product",
            "video_url",
            "embed_code",
            "duration_minutes",
            "sort_order",
            "is_published",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "embed_code": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from documentation.models import DocCategory

        self.fields["category"].queryset = DocCategory.objects.order_by("sort_order", "name")
        self.fields["product"].queryset = Product.objects.order_by("sort_order", "name")


class DocDownloadForm(BaseModelForm):
    class Meta:
        from documentation.models import DocDownload

        model = DocDownload
        fields = [
            "title",
            "description",
            "category",
            "product",
            "file",
            "file_type",
            "version",
            "sort_order",
            "is_published",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from documentation.models import DocCategory

        self.fields["category"].queryset = DocCategory.objects.order_by("sort_order", "name")
        self.fields["product"].queryset = Product.objects.order_by("sort_order", "name")

