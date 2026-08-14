"""Control room documentation management."""

from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from control_room.forms import DocArticleForm, DocCategoryForm, DocDownloadForm, DocVideoForm
from control_room.mixins import ControlRoomMixin, PlatformSettingsMixin
from control_room.services import log_control_change
from documentation.models import DocArticle, DocCategory, DocDownload, DocVideo


class DocumentationHubView(ControlRoomMixin, TemplateView):
    help_key = "documentation"
    template_name = "control_room/documentation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Documentation"},
        ]
        context["stats"] = {
            "categories": DocCategory.objects.count(),
            "articles": DocArticle.objects.count(),
            "videos": DocVideo.objects.count(),
            "downloads": DocDownload.objects.count(),
            "published_articles": DocArticle.objects.filter(is_published=True).count(),
        }
        context["recent_articles"] = DocArticle.objects.select_related("category", "product").order_by("-updated_at")[:8]
        return context


class _DocBreadcrumbMixin:
    section_label = "Documentation"
    section_url_name = "control_room:documentation"

    def get_breadcrumb_items(self, label):
        return [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": self.section_label, "url_name": self.section_url_name},
            {"label": label},
        ]


class DocCategoryListView(ControlRoomMixin, _DocBreadcrumbMixin, ListView):
    help_key = "documentation"
    model = DocCategory
    template_name = "control_room/doc_categories.html"
    context_object_name = "categories"
    paginate_by = 25

    def get_queryset(self):
        return DocCategory.objects.select_related("product").order_by("sort_order", "name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("Categories")
        return context


class DocCategoryCreateView(PlatformSettingsMixin, _DocBreadcrumbMixin, CreateView):
    help_key = "doc_category_form"
    model = DocCategory
    form_class = DocCategoryForm
    template_name = "control_room/doc_form.html"

    def get_success_url(self):
        return reverse("control_room:doc_categories")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("New category")
        context["page_title"] = "New documentation category"
        context["page_subtitle"] = "Group articles, videos, and downloads by topic or product."
        context["cancel_url_name"] = "control_room:doc_categories"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="documentation",
            action="create",
            summary=f"Created doc category: {self.object.name}",
        )
        messages.success(self.request, f"Category “{self.object.name}” created.")
        return response


class DocCategoryUpdateView(PlatformSettingsMixin, _DocBreadcrumbMixin, UpdateView):
    help_key = "doc_category_form"
    model = DocCategory
    form_class = DocCategoryForm
    template_name = "control_room/doc_form.html"

    def get_success_url(self):
        return reverse("control_room:doc_categories")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items(self.object.name)
        context["page_title"] = f"Edit category: {self.object.name}"
        context["page_subtitle"] = "Update category details and publishing status."
        context["cancel_url_name"] = "control_room:doc_categories"
        context["delete_url_name"] = "control_room:doc_category_delete"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="documentation",
            action="update",
            summary=f"Updated doc category: {self.object.name}",
        )
        messages.success(self.request, f"Category “{self.object.name}” saved.")
        return response


class DocCategoryDeleteView(PlatformSettingsMixin, DeleteView):
    model = DocCategory
    success_url = reverse_lazy("control_room:doc_categories")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        log_control_change(
            request.user,
            area="documentation",
            action="delete",
            summary=f"Deleted doc category: {obj.name}",
        )
        messages.success(request, f"Category “{obj.name}” removed.")
        return super().delete(request, *args, **kwargs)


class DocArticleListView(ControlRoomMixin, _DocBreadcrumbMixin, ListView):
    help_key = "documentation"
    model = DocArticle
    template_name = "control_room/doc_articles.html"
    context_object_name = "articles"
    paginate_by = 25

    def get_queryset(self):
        return DocArticle.objects.select_related("category", "product").order_by("-updated_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("Articles")
        return context


class DocArticleCreateView(PlatformSettingsMixin, _DocBreadcrumbMixin, CreateView):
    help_key = "doc_article_form"
    model = DocArticle
    form_class = DocArticleForm
    template_name = "control_room/doc_form.html"

    def get_success_url(self):
        return reverse("control_room:doc_articles")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("New article")
        context["page_title"] = "New documentation article"
        context["page_subtitle"] = "Write guides, FAQs, installation steps, and release notes."
        context["cancel_url_name"] = "control_room:doc_articles"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="documentation",
            action="create",
            summary=f"Created doc article: {self.object.title}",
            details={"article_id": str(self.object.pk), "slug": self.object.slug},
        )
        messages.success(self.request, f"Article “{self.object.title}” created.")
        return response


class DocArticleUpdateView(PlatformSettingsMixin, _DocBreadcrumbMixin, UpdateView):
    help_key = "doc_article_form"
    model = DocArticle
    form_class = DocArticleForm
    template_name = "control_room/doc_form.html"

    def get_success_url(self):
        return reverse("control_room:doc_articles")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items(self.object.title)
        context["page_title"] = f"Edit article: {self.object.title}"
        context["page_subtitle"] = "Update content and publishing settings."
        context["cancel_url_name"] = "control_room:doc_articles"
        context["delete_url_name"] = "control_room:doc_article_delete"
        context["preview_url"] = self.object.get_absolute_url() if self.object.is_published else None
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="documentation",
            action="update",
            summary=f"Updated doc article: {self.object.title}",
            details={"article_id": str(self.object.pk), "slug": self.object.slug},
        )
        messages.success(self.request, f"Article “{self.object.title}” saved.")
        return response


class DocArticleDeleteView(PlatformSettingsMixin, DeleteView):
    model = DocArticle
    success_url = reverse_lazy("control_room:doc_articles")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        log_control_change(
            request.user,
            area="documentation",
            action="delete",
            summary=f"Deleted doc article: {obj.title}",
        )
        messages.success(request, f"Article “{obj.title}” removed.")
        return super().delete(request, *args, **kwargs)


class DocVideoListView(ControlRoomMixin, _DocBreadcrumbMixin, ListView):
    help_key = "documentation"
    model = DocVideo
    template_name = "control_room/doc_videos.html"
    context_object_name = "videos"
    paginate_by = 25

    def get_queryset(self):
        return DocVideo.objects.select_related("category", "product").order_by("sort_order", "title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("Videos")
        return context


class DocVideoCreateView(PlatformSettingsMixin, _DocBreadcrumbMixin, CreateView):
    help_key = "doc_video_form"
    model = DocVideo
    form_class = DocVideoForm
    template_name = "control_room/doc_form.html"

    def get_success_url(self):
        return reverse("control_room:doc_videos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("New video")
        context["page_title"] = "New documentation video"
        context["page_subtitle"] = "Add a YouTube/Vimeo link or paste embed code."
        context["cancel_url_name"] = "control_room:doc_videos"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="documentation",
            action="create",
            summary=f"Created doc video: {self.object.title}",
        )
        messages.success(self.request, f"Video “{self.object.title}” created.")
        return response


class DocVideoUpdateView(PlatformSettingsMixin, _DocBreadcrumbMixin, UpdateView):
    help_key = "doc_video_form"
    model = DocVideo
    form_class = DocVideoForm
    template_name = "control_room/doc_form.html"

    def get_success_url(self):
        return reverse("control_room:doc_videos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items(self.object.title)
        context["page_title"] = f"Edit video: {self.object.title}"
        context["page_subtitle"] = "Update video link, embed code, or publishing status."
        context["cancel_url_name"] = "control_room:doc_videos"
        context["delete_url_name"] = "control_room:doc_video_delete"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="documentation",
            action="update",
            summary=f"Updated doc video: {self.object.title}",
        )
        messages.success(self.request, f"Video “{self.object.title}” saved.")
        return response


class DocVideoDeleteView(PlatformSettingsMixin, DeleteView):
    model = DocVideo
    success_url = reverse_lazy("control_room:doc_videos")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        log_control_change(
            request.user,
            area="documentation",
            action="delete",
            summary=f"Deleted doc video: {obj.title}",
        )
        messages.success(request, f"Video “{obj.title}” removed.")
        return super().delete(request, *args, **kwargs)


class DocDownloadListView(ControlRoomMixin, _DocBreadcrumbMixin, ListView):
    help_key = "documentation"
    model = DocDownload
    template_name = "control_room/doc_downloads.html"
    context_object_name = "downloads"
    paginate_by = 25

    def get_queryset(self):
        return DocDownload.objects.select_related("category", "product").order_by("sort_order", "title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("Downloads")
        return context


class DocDownloadCreateView(PlatformSettingsMixin, _DocBreadcrumbMixin, CreateView):
    help_key = "doc_download_form"
    model = DocDownload
    form_class = DocDownloadForm
    template_name = "control_room/doc_form.html"

    def get_success_url(self):
        return reverse("control_room:doc_downloads")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items("New download")
        context["page_title"] = "New documentation download"
        context["page_subtitle"] = "Upload PDFs, SDKs, sample code, or other files."
        context["cancel_url_name"] = "control_room:doc_downloads"
        context["multipart"] = True
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="documentation",
            action="create",
            summary=f"Created doc download: {self.object.title}",
        )
        messages.success(self.request, f"Download “{self.object.title}” created.")
        return response


class DocDownloadUpdateView(PlatformSettingsMixin, _DocBreadcrumbMixin, UpdateView):
    help_key = "doc_download_form"
    model = DocDownload
    form_class = DocDownloadForm
    template_name = "control_room/doc_form.html"

    def get_success_url(self):
        return reverse("control_room:doc_downloads")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self.get_breadcrumb_items(self.object.title)
        context["page_title"] = f"Edit download: {self.object.title}"
        context["page_subtitle"] = "Replace the file or update metadata."
        context["cancel_url_name"] = "control_room:doc_downloads"
        context["delete_url_name"] = "control_room:doc_download_delete"
        context["multipart"] = True
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="documentation",
            action="update",
            summary=f"Updated doc download: {self.object.title}",
        )
        messages.success(self.request, f"Download “{self.object.title}” saved.")
        return response


class DocDownloadDeleteView(PlatformSettingsMixin, DeleteView):
    model = DocDownload
    success_url = reverse_lazy("control_room:doc_downloads")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        log_control_change(
            request.user,
            area="documentation",
            action="delete",
            summary=f"Deleted doc download: {obj.title}",
        )
        messages.success(request, f"Download “{obj.title}” removed.")
        return super().delete(request, *args, **kwargs)
