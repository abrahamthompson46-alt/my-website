import random
import string

from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from api.mixins import OrganizationAPIMixin
from api.serializers import (
    InvoiceSerializer,
    LicenseSerializer,
    MeSerializer,
    MembershipSerializer,
    OrganizationSerializer,
    SubscriptionSerializer,
    SupportTicketCreateSerializer,
    SupportTicketSerializer,
)
from customer_portal.models import Invoice, License, Subscription, SupportTicket, TicketMessage
from organizations.services import get_user_memberships


class BurstAnonThrottle(AnonRateThrottle):
    scope = "anon_burst"


class SustainedUserThrottle(UserRateThrottle):
    scope = "user_sustained"


class ObtainAuthTokenView(APIView):
    """Issue a DRF auth token for API clients."""

    permission_classes = [AllowAny]
    throttle_classes = [BurstAnonThrottle]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        if not email or not password:
            return Response(
                {"detail": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = authenticate(request, username=email, password=password)
        if user is None:
            # Custom user uses email as USERNAME_FIELD; also try email kw.
            user = authenticate(request, email=email, password=password)
        if user is None or not user.is_active:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": str(user.pk), "email": user.email})


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SustainedUserThrottle]

    def get(self, request):
        memberships = get_user_memberships(request.user)
        payload = {
            "id": request.user.pk,
            "email": request.user.email,
            "display_name": request.user.display_name,
            "memberships": MembershipSerializer(memberships, many=True).data,
        }
        return Response(MeSerializer(payload).data)


class OrganizationListView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SustainedUserThrottle]

    def get(self, request):
        memberships = get_user_memberships(request.user)
        orgs = [m.organization for m in memberships]
        return Response(OrganizationSerializer(orgs, many=True).data)


class SubscriptionListView(OrganizationAPIMixin, generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    throttle_classes = [SustainedUserThrottle]

    def get_queryset(self):
        return (
            Subscription.objects.filter(organization=self.get_organization())
            .select_related("product", "organization")
            .order_by("-started_at")
        )


class InvoiceListView(OrganizationAPIMixin, generics.ListAPIView):
    serializer_class = InvoiceSerializer
    throttle_classes = [SustainedUserThrottle]

    def get_queryset(self):
        return (
            Invoice.objects.filter(organization=self.get_organization())
            .select_related("organization")
            .order_by("-issued_at")
        )


class InvoiceDetailView(OrganizationAPIMixin, generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    throttle_classes = [SustainedUserThrottle]
    lookup_field = "pk"

    def get_queryset(self):
        return Invoice.objects.filter(organization=self.get_organization())


class LicenseListView(OrganizationAPIMixin, generics.ListAPIView):
    serializer_class = LicenseSerializer
    throttle_classes = [SustainedUserThrottle]

    def get_queryset(self):
        return (
            License.objects.filter(organization=self.get_organization())
            .select_related("product", "organization")
            .order_by("-created_at")
        )


class SupportTicketListCreateView(OrganizationAPIMixin, generics.ListCreateAPIView):
    throttle_classes = [SustainedUserThrottle]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SupportTicketCreateSerializer
        return SupportTicketSerializer

    def get_queryset(self):
        return (
            SupportTicket.objects.filter(organization=self.get_organization())
            .select_related("product", "organization")
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output = SupportTicketSerializer(serializer.instance, context=self.get_serializer_context())
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        organization = self.get_organization()
        reference = self._generate_reference()
        ticket = serializer.save(
            user=self.request.user,
            organization=organization,
            reference=reference,
        )
        TicketMessage.objects.create(
            ticket=ticket,
            author=self.request.user,
            body=ticket.description,
            is_staff=False,
        )

    def _generate_reference(self):
        while True:
            ref = "TKT-" + "".join(random.choices(string.digits, k=6))
            if not SupportTicket.objects.filter(reference=ref).exists():
                return ref


class SupportTicketDetailView(OrganizationAPIMixin, generics.RetrieveAPIView):
    serializer_class = SupportTicketSerializer
    throttle_classes = [SustainedUserThrottle]
    lookup_field = "pk"

    def get_queryset(self):
        return SupportTicket.objects.filter(organization=self.get_organization())
