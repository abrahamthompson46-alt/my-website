from rest_framework import serializers

from customer_portal.models import Invoice, License, Subscription, SupportTicket
from organizations.models import Organization, OrganizationMembership


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "status", "created_at")
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ("id", "organization", "role", "status", "joined_at")
        read_only_fields = fields


class MeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    display_name = serializers.CharField()
    memberships = MembershipSerializer(many=True)


class SubscriptionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "product_name",
            "product_slug",
            "plan_name",
            "status",
            "billing_interval",
            "amount",
            "currency",
            "started_at",
            "renews_at",
            "trial_ends_at",
            "organization",
        )
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_number",
            "description",
            "amount",
            "currency",
            "status",
            "issued_at",
            "due_at",
            "paid_at",
            "organization",
        )
        read_only_fields = fields


class LicenseSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = License
        fields = (
            "id",
            "product_name",
            "license_key",
            "status",
            "seats",
            "activated_at",
            "expires_at",
            "organization",
        )
        read_only_fields = fields


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = (
            "id",
            "reference",
            "subject",
            "description",
            "status",
            "priority",
            "product",
            "organization",
            "created_at",
        )
        read_only_fields = ("id", "reference", "status", "organization", "created_at")


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ("subject", "description", "priority", "product")
