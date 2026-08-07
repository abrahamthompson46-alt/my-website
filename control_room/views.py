from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from control_room.forms import (
    FeatureFlagForm,
    NavigationMenuForm,
    PlatformSettingsForm,
    RedirectRuleForm,
    SiteAnnouncementForm,
)
from control_room.mixins import ControlRoomMixin
from control_room.models import (
    ControlChangeLog,
    FeatureFlag,
    NavigationMenu,
    PlatformSettings,
    RedirectRule,
    SiteAnnouncement,
)
from control_room.services import (
    get_content_registry,
    get_platform_settings,
    invalidate_navigation_cache,
    invalidate_platform_settings_cache,
    log_control_change,
)
from control_room.services.seeds import get_seed_registry, run_all_seeds, run_seed_by_key


class DashboardView(ControlRoomMixin, TemplateView):
    template_name = "control_room/dashboard.html"

    def get_context_data(self, **kwargs):
        from control_room.services.cache_health import get_cache_diagnostics
        from operations.services.dashboard import get_overview_stats
        from operations.services.health import get_system_health

        context = super().get_context_data(**kwargs)
        settings_obj = get_platform_settings()
        context["platform_settings"] = settings_obj
        context["stats"] = {
            "navigation_menus": NavigationMenu.objects.filter(is_active=True).count(),
            "redirects": RedirectRule.objects.filter(is_active=True).count(),
            "announcements": SiteAnnouncement.objects.filter(is_active=True).count(),
            "feature_flags": FeatureFlag.objects.filter(is_enabled=True).count(),
            "recent_changes": ControlChangeLog.objects.count(),
        }
        context["business_stats"] = get_overview_stats()
        context["health"] = get_system_health()
        context["cache_diagnostics"] = get_cache_diagnostics()
        context["recent_changes"] = ControlChangeLog.objects.select_related("user")[:6]
        context["seed_registry"] = get_seed_registry()
        context["seed_groups"] = self._group_seeds(get_seed_registry())
        context["last_seed_results"] = self.request.session.pop("last_seed_results", None)
        context["control_modules"] = [
            {"title": "Site Settings", "description": "Branding, SEO, contact, maintenance", "url_name": "control_room:settings", "icon": "settings", "accent": "gold"},
            {"title": "Navigation", "description": "Header, footer, portal menus", "url_name": "control_room:navigation", "icon": "menu", "accent": "blue"},
            {"title": "Redirects", "description": "URL rules without deploys", "url_name": "control_room:redirects", "icon": "external-link", "accent": "teal"},
            {"title": "Announcements", "description": "Public & portal banners", "url_name": "control_room:announcements", "icon": "bell", "accent": "amber"},
            {"title": "Feature Flags", "description": "Toggle platform capabilities", "url_name": "control_room:flags", "icon": "zap", "accent": "violet"},
            {"title": "Products", "description": "Create catalog entries, upload media, track demos", "url_name": "control_room:products", "icon": "package", "accent": "teal"},
            {"title": "Content Hub", "description": "All content domains", "url_name": "control_room:content", "icon": "layers", "accent": "navy"},
            {"title": "Platform Setup", "description": "One-click seed & bootstrap", "url_name": "control_room:setup", "icon": "database", "accent": "green"},
            {"title": "Ops Dashboard", "description": "Revenue, customers, tickets", "url_name": "operations:dashboard", "icon": "bar-chart-2", "accent": "blue"},
        ]
        context["breadcrumb_items"] = [{"label": "Super Dashboard"}]
        return context

    @staticmethod
    def _group_seeds(registry):
        groups = {}
        for item in registry:
            groups.setdefault(item["group"], []).append(item)
        return groups


class SettingsView(ControlRoomMixin, UpdateView):
    model = PlatformSettings
    form_class = PlatformSettingsForm
    template_name = "control_room/settings.html"
    success_url = reverse_lazy("control_room:settings")

    def get_object(self, queryset=None):
        return PlatformSettings.load()

    def get_context_data(self, **kwargs):
        from control_room.services.theme import THEME_PRESETS

        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Site Settings"},
        ]
        context["theme_presets_json"] = {
            key: {"primary": data["primary"], "accent": data["accent"]}
            for key, data in THEME_PRESETS.items()
            if key != "custom"
        }
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        invalidate_platform_settings_cache()
        log_control_change(
            self.request.user,
            area="platform_settings",
            action="update",
            summary="Updated platform settings",
            details={"fields": list(form.changed_data)},
        )
        messages.success(self.request, "Platform settings saved. Changes apply site-wide immediately.")
        return response


class NavigationListView(ControlRoomMixin, ListView):
    model = NavigationMenu
    template_name = "control_room/navigation_list.html"
    context_object_name = "menus"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Navigation"},
        ]
        return context


class NavigationEditView(ControlRoomMixin, UpdateView):
    model = NavigationMenu
    form_class = NavigationMenuForm
    template_name = "control_room/navigation_edit.html"
    context_object_name = "menu"

    def get_success_url(self):
        return reverse("control_room:navigation_edit", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Navigation", "url_name": "control_room:navigation"},
            {"label": self.object.name},
        ]
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        invalidate_navigation_cache(self.object.code)
        log_control_change(
            self.request.user,
            area="navigation",
            action="update",
            summary=f"Updated navigation menu: {self.object.code}",
        )
        messages.success(self.request, f"Navigation “{self.object.name}” updated.")
        return response


class RedirectListView(ControlRoomMixin, ListView):
    model = RedirectRule
    template_name = "control_room/redirects.html"
    context_object_name = "redirects"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = RedirectRuleForm()
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Redirects"},
        ]
        return context


class RedirectCreateView(ControlRoomMixin, CreateView):
    model = RedirectRule
    form_class = RedirectRuleForm
    template_name = "control_room/redirect_form.html"

    def get_success_url(self):
        return reverse("control_room:redirects")

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="redirects",
            action="create",
            summary=f"Created redirect {self.object.from_path}",
        )
        messages.success(self.request, "Redirect rule created.")
        return response


class RedirectUpdateView(ControlRoomMixin, UpdateView):
    model = RedirectRule
    form_class = RedirectRuleForm
    template_name = "control_room/redirect_form.html"

    def get_success_url(self):
        return reverse("control_room:redirects")

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="redirects",
            action="update",
            summary=f"Updated redirect {self.object.from_path}",
        )
        messages.success(self.request, "Redirect rule updated.")
        return response


class RedirectDeleteView(ControlRoomMixin, DeleteView):
    model = RedirectRule

    def get_success_url(self):
        return reverse("control_room:redirects")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        log_control_change(
            request.user,
            area="redirects",
            action="delete",
            summary=f"Deleted redirect {obj.from_path}",
        )
        messages.success(request, "Redirect rule removed.")
        return super().delete(request, *args, **kwargs)


class AnnouncementListView(ControlRoomMixin, ListView):
    model = SiteAnnouncement
    template_name = "control_room/announcements.html"
    context_object_name = "announcements"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SiteAnnouncementForm()
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Announcements"},
        ]
        return context


class AnnouncementCreateView(ControlRoomMixin, CreateView):
    model = SiteAnnouncement
    form_class = SiteAnnouncementForm
    template_name = "control_room/announcement_form.html"

    def get_success_url(self):
        return reverse("control_room:announcements")

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="announcements",
            action="create",
            summary=f"Created announcement: {self.object.title}",
        )
        messages.success(self.request, "Announcement published.")
        return response


class AnnouncementUpdateView(ControlRoomMixin, UpdateView):
    model = SiteAnnouncement
    form_class = SiteAnnouncementForm
    template_name = "control_room/announcement_form.html"

    def get_success_url(self):
        return reverse("control_room:announcements")

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="announcements",
            action="update",
            summary=f"Updated announcement: {self.object.title}",
        )
        messages.success(self.request, "Announcement updated.")
        return response


class AnnouncementDeleteView(ControlRoomMixin, DeleteView):
    model = SiteAnnouncement

    def get_success_url(self):
        return reverse("control_room:announcements")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        log_control_change(
            request.user,
            area="announcements",
            action="delete",
            summary=f"Deleted announcement: {obj.title}",
        )
        messages.success(request, "Announcement removed.")
        return super().delete(request, *args, **kwargs)


class FeatureFlagListView(ControlRoomMixin, ListView):
    model = FeatureFlag
    template_name = "control_room/flags.html"
    context_object_name = "flags"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = FeatureFlagForm()
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Feature Flags"},
        ]
        return context


class FeatureFlagCreateView(ControlRoomMixin, CreateView):
    model = FeatureFlag
    form_class = FeatureFlagForm
    template_name = "control_room/flag_form.html"

    def get_success_url(self):
        return reverse("control_room:flags")

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="feature_flags",
            action="create",
            summary=f"Created feature flag: {self.object.key}",
        )
        messages.success(self.request, "Feature flag created.")
        return response


class FeatureFlagUpdateView(ControlRoomMixin, UpdateView):
    model = FeatureFlag
    form_class = FeatureFlagForm
    template_name = "control_room/flag_form.html"

    def get_success_url(self):
        return reverse("control_room:flags")

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="feature_flags",
            action="update",
            summary=f"Updated feature flag: {self.object.key}",
        )
        messages.success(self.request, "Feature flag updated.")
        return response


class FeatureFlagToggleView(ControlRoomMixin, TemplateView):
    def post(self, request, pk):
        flag = get_object_or_404(FeatureFlag, pk=pk)
        flag.is_enabled = not flag.is_enabled
        flag.save(update_fields=["is_enabled", "updated_at"])
        log_control_change(
            request.user,
            area="feature_flags",
            action="toggle",
            summary=f"{'Enabled' if flag.is_enabled else 'Disabled'} {flag.key}",
        )
        messages.success(request, f"Feature “{flag.label}” is now {'on' if flag.is_enabled else 'off'}.")
        return redirect("control_room:flags")


class ContentHubView(ControlRoomMixin, TemplateView):
    template_name = "control_room/content.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["registry"] = get_content_registry()
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Content Hub"},
        ]
        return context


class ChangeLogView(ControlRoomMixin, ListView):
    model = ControlChangeLog
    template_name = "control_room/changelog.html"
    context_object_name = "changes"
    paginate_by = 40

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Super Dashboard", "url_name": "control_room:dashboard"},
            {"label": "Change Log"},
        ]
        return context


class SetupView(ControlRoomMixin, TemplateView):
    template_name = "control_room/setup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registry = get_seed_registry()
        context["seed_registry"] = registry
        context["seed_groups"] = DashboardView._group_seeds(registry)
        context["last_seed_results"] = self.request.session.pop("last_seed_results", None)
        context["breadcrumb_items"] = [
            {"label": "Super Dashboard", "url_name": "control_room:dashboard"},
            {"label": "Platform Setup"},
        ]
        return context


class SeedRunView(ControlRoomMixin, TemplateView):
    def post(self, request, key):
        result = run_seed_by_key(key)
        self._persist_results(request, [result], key)
        return redirect(request.POST.get("next") or "control_room:setup")

    def _persist_results(self, request, results, key=None):
        request.session["last_seed_results"] = results
        if all(r.get("ok") for r in results):
            title = results[0].get("title") or key or "Seed"
            messages.success(request, f"{title} completed successfully.")
            log_control_change(
                request.user,
                area="platform_setup",
                action="seed",
                summary=f"Ran seed: {key or 'all'}",
                details={"results": [{k: v for k, v in r.items() if k != "output"} for r in results]},
            )
        else:
            failed = next(r for r in results if not r.get("ok"))
            messages.error(request, f"Seed failed: {failed.get('error') or failed.get('title', key)}")


class SeedRunAllView(ControlRoomMixin, TemplateView):
    def post(self, request):
        results = run_all_seeds()
        request.session["last_seed_results"] = results
        ok_count = sum(1 for r in results if r.get("ok"))
        if ok_count == len(results):
            messages.success(request, f"All {len(results)} platform seeds completed successfully.")
            log_control_change(
                request.user,
                area="platform_setup",
                action="seed_all",
                summary=f"Ran all platform seeds ({len(results)} commands)",
            )
        else:
            messages.warning(request, f"Completed {ok_count}/{len(results)} seeds. Review the output log below.")
        return redirect(request.POST.get("next") or "control_room:setup")
