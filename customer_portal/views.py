from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView, View

from accounts.forms import PortalPasswordChangeForm, MFADisableForm
from accounts.models import AuditEventType
from accounts.services.audit import log_audit_event
from accounts.services.email import get_or_create_security_profile
from accounts.services.sessions import get_active_sessions
from customer_portal.forms import (
    ProfileForm,
    SupportTicketForm,
    TicketReplyForm,
    UserNameForm,
)
from customer_portal.mixins import PortalMixin, UserQuerysetMixin
from customer_portal.models import (
    CustomerDownload,
    Invoice,
    License,
    PortalNotification,
    ProductUpdate,
    Subscription,
    SupportTicket,
    TicketMessage,
)
from customer_portal.services import (
    get_dashboard_stats,
    get_or_create_profile,
    get_product_updates_for_user,
    get_recent_notifications,
    get_subscribed_products,
)
from products.models import Product


class DashboardView(PortalMixin, TemplateView):
    template_name = "customer_portal/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["stats"] = get_dashboard_stats(user)
        context["subscriptions"] = Subscription.objects.filter(user=user).select_related("product")[:4]
        context["recent_invoices"] = Invoice.objects.filter(user=user).order_by("-issued_at")[:5]
        context["recent_tickets"] = SupportTicket.objects.filter(user=user).order_by("-created_at")[:5]
        context["recent_updates"] = get_product_updates_for_user(user, limit=4)
        context["notifications"] = get_recent_notifications(user, limit=5)
        context["breadcrumb_items"] = [{"label": "Dashboard"}]
        return context


class SubscriptionListView(PortalMixin, UserQuerysetMixin, ListView):
    model = Subscription
    template_name = "customer_portal/subscriptions.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        return super().get_queryset().select_related("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Subscriptions"},
        ]
        return context


class LicenseListView(PortalMixin, UserQuerysetMixin, ListView):
    model = License
    template_name = "customer_portal/licenses.html"
    context_object_name = "licenses"

    def get_queryset(self):
        return super().get_queryset().select_related("product", "subscription")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Licenses"},
        ]
        return context


class InvoiceListView(PortalMixin, UserQuerysetMixin, ListView):
    model = Invoice
    template_name = "customer_portal/invoices.html"
    context_object_name = "invoices"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Invoices"},
        ]
        return context


class InvoiceDetailView(PortalMixin, UserQuerysetMixin, DetailView):
    model = Invoice
    template_name = "customer_portal/invoice_detail.html"
    context_object_name = "invoice"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Invoices", "url_name": "customer_portal:invoices"},
            {"label": self.object.invoice_number},
        ]
        return context


class DownloadListView(PortalMixin, UserQuerysetMixin, ListView):
    model = CustomerDownload
    template_name = "customer_portal/downloads.html"
    context_object_name = "downloads"

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True).select_related("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Downloads"},
        ]
        return context


class TicketListView(PortalMixin, UserQuerysetMixin, ListView):
    model = SupportTicket
    template_name = "customer_portal/tickets.html"
    context_object_name = "tickets"

    def get_queryset(self):
        return super().get_queryset().select_related("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Support Tickets"},
        ]
        return context


class TicketCreateView(PortalMixin, TemplateView):
    template_name = "customer_portal/ticket_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form", SupportTicketForm(user=self.request.user))
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Support Tickets", "url_name": "customer_portal:tickets"},
            {"label": "New Ticket"},
        ]
        return context

    def post(self, request, *args, **kwargs):
        form = SupportTicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.reference = self._generate_reference()
            ticket.save()
            TicketMessage.objects.create(
                ticket=ticket,
                author=request.user,
                body=ticket.description,
                is_staff=False,
            )
            messages.success(request, f"Ticket {ticket.reference} created successfully.")
            return redirect("customer_portal:ticket_detail", pk=ticket.pk)
        return self.render_to_response(self.get_context_data(form=form))

    def _generate_reference(self):
        import random
        import string

        while True:
            ref = "TKT-" + "".join(random.choices(string.digits, k=6))
            if not SupportTicket.objects.filter(reference=ref).exists():
                return ref


class TicketDetailView(PortalMixin, UserQuerysetMixin, DetailView):
    model = SupportTicket
    template_name = "customer_portal/ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("messages__author", "product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reply_form"] = kwargs.get("reply_form", TicketReplyForm())
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Support Tickets", "url_name": "customer_portal:tickets"},
            {"label": self.object.reference},
        ]
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = TicketReplyForm(request.POST)
        if form.is_valid():
            TicketMessage.objects.create(
                ticket=self.object,
                author=request.user,
                body=form.cleaned_data["body"],
                is_staff=False,
            )
            if self.object.status in {"resolved", "closed"}:
                self.object.status = "open"
                self.object.save(update_fields=["status", "updated_at"])
            messages.success(request, "Reply sent.")
            return redirect("customer_portal:ticket_detail", pk=self.object.pk)
        return self.render_to_response(self.get_context_data(reply_form=form))


class ProductUpdateListView(PortalMixin, ListView):
    model = ProductUpdate
    template_name = "customer_portal/updates.html"
    context_object_name = "updates"

    def get_queryset(self):
        product_ids = Subscription.objects.filter(
            user=self.request.user, status__in=["active", "trial"]
        ).values_list("product_id", flat=True)
        return ProductUpdate.objects.filter(
            product_id__in=product_ids, is_published=True
        ).select_related("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Product Updates"},
        ]
        return context


class DocumentationView(PortalMixin, TemplateView):
    template_name = "customer_portal/documentation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscriptions = get_subscribed_products(self.request.user)
        products = []
        for sub in subscriptions:
            product = sub.product
            if product.documentation_url:
                docs_url = product.documentation_url
            else:
                docs_url = reverse("documentation:index") + f"?product={product.slug}"
            products.append(
                {
                    "product": product,
                    "documentation_url": docs_url,
                    "plan": sub.plan_name,
                }
            )
        if not products:
            products = [
                {
                    "product": p,
                    "documentation_url": p.documentation_url or reverse("documentation:index") + f"?product={p.slug}",
                    "plan": None,
                }
                for p in Product.objects.filter(is_published=True).order_by("sort_order")[:6]
            ]
        context["products"] = products
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Documentation"},
        ]
        return context


class NotificationListView(PortalMixin, UserQuerysetMixin, ListView):
    model = PortalNotification
    template_name = "customer_portal/notifications.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Notifications"},
        ]
        return context


class NotificationMarkReadView(PortalMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(PortalNotification, pk=pk, user=request.user)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at", "updated_at"])
        if notification.link_url:
            return redirect(notification.link_url)
        return redirect("customer_portal:notifications")


class NotificationMarkAllReadView(PortalMixin, View):
    def post(self, request):
        PortalNotification.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        messages.success(request, "All notifications marked as read.")
        return redirect("customer_portal:notifications")


class ProfileView(PortalMixin, TemplateView):
    template_name = "customer_portal/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_or_create_profile(self.request.user)
        context["profile"] = profile
        context["profile_form"] = kwargs.get("profile_form", ProfileForm(instance=profile))
        context["name_form"] = kwargs.get(
            "name_form",
            UserNameForm(
                initial={
                    "first_name": self.request.user.first_name,
                    "last_name": self.request.user.last_name,
                }
            ),
        )
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Profile"},
        ]
        return context

    def post(self, request, *args, **kwargs):
        profile = get_or_create_profile(request.user)
        if "save_profile" in request.POST:
            form = ProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated.")
                return redirect("customer_portal:profile")
            return self.render_to_response(self.get_context_data(profile_form=form))
        if "save_name" in request.POST:
            form = UserNameForm(request.POST)
            if form.is_valid():
                request.user.first_name = form.cleaned_data["first_name"]
                request.user.last_name = form.cleaned_data["last_name"]
                request.user.save(update_fields=["first_name", "last_name"])
                messages.success(request, "Name updated.")
                return redirect("customer_portal:profile")
            return self.render_to_response(self.get_context_data(name_form=form))
        return redirect("customer_portal:profile")


class SecuritySettingsView(PortalMixin, TemplateView):
    template_name = "customer_portal/security.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["password_form"] = kwargs.get(
            "password_form", PortalPasswordChangeForm(user=self.request.user)
        )
        context["security_profile"] = get_or_create_security_profile(self.request.user)
        context["mfa_disable_form"] = kwargs.get("mfa_disable_form", MFADisableForm())
        context["active_sessions"] = get_active_sessions(self.request.user)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Security Settings"},
        ]
        return context

    def post(self, request, *args, **kwargs):
        if "change_password" not in request.POST:
            return redirect("customer_portal:security")
        form = PortalPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            profile = get_or_create_security_profile(request.user)
            from django.utils import timezone

            profile.password_changed_at = timezone.now()
            profile.save(update_fields=["password_changed_at", "updated_at"])
            log_audit_event(AuditEventType.PASSWORD_CHANGED, request=request, user=request.user)
            messages.success(request, "Password updated successfully.")
            return redirect("customer_portal:security")
        return self.render_to_response(self.get_context_data(password_form=form))
