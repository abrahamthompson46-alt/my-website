"""Control room product media management (screenshots, templates, videos)."""

import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from control_room.forms import ProductScreenshotForm, ProductVideoForm
from control_room.mixins import ControlRoomMixin, PlatformSettingsMixin
from control_room.services import log_control_change
from products.models import Product
from products.models.media import ProductScreenshot, ProductVideo, ScreenshotKind

logger = logging.getLogger(__name__)


class _ProductMediaMixin:
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs["product_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_breadcrumb_items(self, label):
        return [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Products", "url_name": "control_room:products"},
            {
                "label": self.product.name,
                "url_name": "control_room:product_detail",
                "url_kwargs": {"pk": self.product.pk},
            },
            {"label": label},
        ]

    def _save_uploaded_media(self, form, *, product_field: bool = True):
        """
        Persist an uploaded media object, converting storage failures into form errors
        instead of an unhandled 500 (common when MEDIA_ROOT is not writable).
        """
        self.object = form.save(commit=False)
        if product_field:
            self.object.product = self.product
        try:
            self.object.save()
        except OSError as exc:
            logger.exception(
                "Media upload failed for product=%s user=%s",
                getattr(self.product, "slug", None),
                getattr(self.request.user, "pk", None),
            )
            field = "image" if "image" in form.fields else ("thumbnail" if "thumbnail" in form.fields else None)
            message = (
                "Could not save the file on the server. Media storage may be missing "
                "write permission for the app user. Ask an operator to run: "
                "sudo chown -R marketing:marketing-runtime /var/www/marketing-site/media "
                "&& sudo chmod -R ug+rwX /var/www/marketing-site/media"
            )
            if field:
                form.add_error(field, message)
            else:
                form.add_error(None, message)
            # Surface the exception class for operators without leaking paths.
            form.add_error(None, f"Storage error: {exc.__class__.__name__}.")
            return None
        return self.object


class ProductScreenshotListView(ControlRoomMixin, _ProductMediaMixin, ListView):
    help_key = "product_media"
    model = ProductScreenshot
    template_name = "control_room/product_screenshots.html"
    context_object_name = "screenshots"
    paginate_by = 25

    def get_queryset(self):
        qs = ProductScreenshot.objects.filter(product=self.product)
        self.media_kind = self.request.GET.get("kind", ScreenshotKind.SCREENSHOT)
        if self.media_kind in dict(ScreenshotKind.choices):
            qs = qs.filter(kind=self.media_kind)
        return qs.order_by("sort_order", "title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kind_label = dict(ScreenshotKind.choices).get(self.media_kind, "Screenshots")
        context["breadcrumb_items"] = self.get_breadcrumb_items(kind_label)
        context["product"] = self.product
        context["media_kind"] = self.media_kind
        context["media_kind_label"] = kind_label
        context["create_url"] = reverse(
            "control_room:product_screenshot_create",
            kwargs={"product_pk": self.product.pk},
        ) + f"?kind={self.media_kind}"
        return context


class ProductScreenshotCreateView(PlatformSettingsMixin, _ProductMediaMixin, CreateView):
    help_key = "product_media_form"
    model = ProductScreenshot
    form_class = ProductScreenshotForm
    template_name = "control_room/product_media_form.html"

    def get_initial(self):
        kind = self.request.GET.get("kind", ScreenshotKind.SCREENSHOT)
        if kind in dict(ScreenshotKind.choices):
            return {"kind": kind}
        return {}

    def get_success_url(self):
        return (
            reverse("control_room:product_screenshots", kwargs={"product_pk": self.product.pk})
            + f"?kind={self.object.kind}"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("New screenshot")
        context["page_title"] = "New product screenshot"
        context["page_subtitle"] = f"Upload media for {self.product.name}."
        context["cancel_url_name"] = "control_room:product_screenshots"
        context["cancel_url_kwargs"] = {"product_pk": self.product.pk}
        context["multipart"] = True
        return context

    def form_valid(self, form):
        if self._save_uploaded_media(form) is None:
            return self.form_invalid(form)
        log_control_change(
            self.request.user,
            area="products",
            action="create",
            summary=f"Added {self.object.get_kind_display().lower()} for {self.product.name}",
            details={"product_id": str(self.product.pk), "screenshot_id": str(self.object.pk)},
        )
        messages.success(self.request, f"“{self.object.alt_text}” uploaded.")
        return redirect(self.get_success_url())


class ProductScreenshotUpdateView(PlatformSettingsMixin, _ProductMediaMixin, UpdateView):
    help_key = "product_media_form"
    model = ProductScreenshot
    form_class = ProductScreenshotForm
    template_name = "control_room/product_media_form.html"
    context_object_name = "screenshot"

    def get_queryset(self):
        return ProductScreenshot.objects.filter(product=self.product)

    def get_success_url(self):
        return (
            reverse("control_room:product_screenshots", kwargs={"product_pk": self.product.pk})
            + f"?kind={self.object.kind}"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items(self.object.alt_text)
        context["page_title"] = f"Edit {self.object.get_kind_display().lower()}"
        context["page_subtitle"] = f"Update media for {self.product.name}."
        context["cancel_url_name"] = "control_room:product_screenshots"
        context["cancel_url_kwargs"] = {"product_pk": self.product.pk}
        context["delete_url_name"] = "control_room:product_screenshot_delete"
        context["delete_url_kwargs"] = {"product_pk": self.product.pk, "pk": self.object.pk}
        context["multipart"] = True
        return context

    def form_valid(self, form):
        if self._save_uploaded_media(form, product_field=False) is None:
            return self.form_invalid(form)
        log_control_change(
            self.request.user,
            area="products",
            action="update",
            summary=f"Updated {self.object.get_kind_display().lower()} for {self.product.name}",
            details={"product_id": str(self.product.pk), "screenshot_id": str(self.object.pk)},
        )
        messages.success(self.request, "Screenshot saved.")
        return redirect(self.get_success_url())


class ProductScreenshotDeleteView(PlatformSettingsMixin, _ProductMediaMixin, DeleteView):
    model = ProductScreenshot

    def get_queryset(self):
        return ProductScreenshot.objects.filter(product=self.product)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        kind = obj.kind
        log_control_change(
            request.user,
            area="products",
            action="delete",
            summary=f"Deleted {obj.get_kind_display().lower()} for {self.product.name}",
            details={"product_id": str(self.product.pk), "screenshot_id": str(obj.pk)},
        )
        messages.success(request, "Media item removed.")
        response = super().delete(request, *args, **kwargs)
        return response

    def get_success_url(self):
        kind = getattr(self, "object", None)
        kind_param = kind.kind if kind else ScreenshotKind.SCREENSHOT
        return (
            reverse("control_room:product_screenshots", kwargs={"product_pk": self.product.pk})
            + f"?kind={kind_param}"
        )


class ProductVideoListView(ControlRoomMixin, _ProductMediaMixin, ListView):
    help_key = "product_media"
    model = ProductVideo
    template_name = "control_room/product_videos.html"
    context_object_name = "videos"
    paginate_by = 25

    def get_queryset(self):
        return ProductVideo.objects.filter(product=self.product).order_by("sort_order", "title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("Videos")
        context["product"] = self.product
        return context


class ProductVideoCreateView(PlatformSettingsMixin, _ProductMediaMixin, CreateView):
    help_key = "product_media_form"
    model = ProductVideo
    form_class = ProductVideoForm
    template_name = "control_room/product_media_form.html"

    def get_success_url(self):
        return reverse("control_room:product_videos", kwargs={"product_pk": self.product.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("New video")
        context["page_title"] = "New product video"
        context["page_subtitle"] = f"Add a walkthrough or promo video for {self.product.name}."
        context["cancel_url_name"] = "control_room:product_videos"
        context["cancel_url_kwargs"] = {"product_pk": self.product.pk}
        context["multipart"] = True
        return context

    def form_valid(self, form):
        if self._save_uploaded_media(form) is None:
            return self.form_invalid(form)
        log_control_change(
            self.request.user,
            area="products",
            action="create",
            summary=f"Added video for {self.product.name}",
            details={"product_id": str(self.product.pk), "video_id": str(self.object.pk)},
        )
        messages.success(self.request, f"Video “{self.object.title}” created.")
        return redirect(self.get_success_url())


class ProductVideoUpdateView(PlatformSettingsMixin, _ProductMediaMixin, UpdateView):
    help_key = "product_media_form"
    model = ProductVideo
    form_class = ProductVideoForm
    template_name = "control_room/product_media_form.html"
    context_object_name = "video"

    def get_queryset(self):
        return ProductVideo.objects.filter(product=self.product)

    def get_success_url(self):
        return reverse("control_room:product_videos", kwargs={"product_pk": self.product.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items(self.object.title)
        context["page_title"] = f"Edit video: {self.object.title}"
        context["page_subtitle"] = f"Update video details for {self.product.name}."
        context["cancel_url_name"] = "control_room:product_videos"
        context["cancel_url_kwargs"] = {"product_pk": self.product.pk}
        context["delete_url_name"] = "control_room:product_video_delete"
        context["delete_url_kwargs"] = {"product_pk": self.product.pk, "pk": self.object.pk}
        context["multipart"] = True
        return context

    def form_valid(self, form):
        if self._save_uploaded_media(form, product_field=False) is None:
            return self.form_invalid(form)
        log_control_change(
            self.request.user,
            area="products",
            action="update",
            summary=f"Updated video for {self.product.name}",
            details={"product_id": str(self.product.pk), "video_id": str(self.object.pk)},
        )
        messages.success(self.request, "Video saved.")
        return redirect(self.get_success_url())


class ProductVideoDeleteView(PlatformSettingsMixin, _ProductMediaMixin, DeleteView):
    model = ProductVideo

    def get_queryset(self):
        return ProductVideo.objects.filter(product=self.product)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        log_control_change(
            request.user,
            area="products",
            action="delete",
            summary=f"Deleted video for {self.product.name}",
            details={"product_id": str(self.product.pk), "video_id": str(obj.pk)},
        )
        messages.success(request, f"Video “{obj.title}” removed.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("control_room:product_videos", kwargs={"product_pk": self.product.pk})
