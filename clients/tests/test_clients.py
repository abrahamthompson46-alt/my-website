from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from clients.exceptions import (
    ClientNotFoundError,
    DuplicateClientError,
    InvalidClientStatusError,
)
from clients.models import ClientStatus, ClientType
from clients.services import (
    clients_for_organization,
    create_client,
    deactivate_client,
    get_client_for_organization,
    next_client_number,
    set_client_status,
    update_client,
)
from organizations.services import create_organization


User = get_user_model()


class ClientManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="loan_officer",
            email="officer@example.com",
            password="SecurePass123!",
        )
        self.org = create_organization(name="Borrower Org", created_by=self.user)
        self.other_org = create_organization(name="Other MFI", created_by=self.user)

    def test_create_individual_client_auto_number(self):
        client = create_client(
            organization=self.org,
            first_name="Ama",
            last_name="Mensah",
            phone="+233201112233",
            national_id="GHA-123456789-0",
            created_by=self.user,
        )
        self.assertEqual(client.client_number, "CL-000001")
        self.assertEqual(client.display_name, "Ama Mensah")
        self.assertEqual(client.client_type, ClientType.INDIVIDUAL)
        self.assertEqual(client.status, ClientStatus.ACTIVE)
        self.assertEqual(next_client_number(self.org), "CL-000002")

    def test_create_business_and_group_clients(self):
        biz = create_client(
            organization=self.org,
            client_type=ClientType.BUSINESS,
            display_name="Sunrise Traders Ltd",
            phone="+233209998877",
        )
        group = create_client(
            organization=self.org,
            client_type=ClientType.GROUP,
            display_name="Adenta Solidarity Group",
        )
        self.assertEqual(biz.client_type, ClientType.BUSINESS)
        self.assertEqual(group.client_type, ClientType.GROUP)
        self.assertEqual(clients_for_organization(self.org).count(), 2)

    def test_duplicate_client_number_rejected(self):
        create_client(
            organization=self.org,
            display_name="One",
            client_number="CL-000010",
        )
        with self.assertRaises(DuplicateClientError):
            create_client(
                organization=self.org,
                display_name="Two",
                client_number="CL-000010",
            )

    def test_duplicate_national_id_per_org_rejected(self):
        create_client(
            organization=self.org,
            display_name="One",
            national_id="NID-1",
        )
        create_client(
            organization=self.other_org,
            display_name="Other One",
            national_id="NID-1",
        )
        with self.assertRaises(DuplicateClientError):
            create_client(
                organization=self.org,
                display_name="Two",
                national_id="NID-1",
            )

    def test_tenant_isolation_for_get_and_list(self):
        local = create_client(
            organization=self.org,
            display_name="Local Client",
            phone="111",
        )
        create_client(
            organization=self.other_org,
            display_name="Remote Client",
            phone="222",
        )
        self.assertEqual(clients_for_organization(self.org).count(), 1)
        self.assertEqual(
            get_client_for_organization(self.org, local.id).display_name,
            "Local Client",
        )
        with self.assertRaises(ClientNotFoundError):
            get_client_for_organization(self.other_org, local.id)

    def test_update_and_deactivate_client(self):
        client = create_client(
            organization=self.org,
            first_name="Kofi",
            last_name="Owusu",
            city="Accra",
        )
        update_client(
            client,
            organization=self.org,
            phone="+233200000001",
            city="Kumasi",
            date_of_birth=date(1990, 5, 1),
        )
        client.refresh_from_db()
        self.assertEqual(client.phone, "+233200000001")
        self.assertEqual(client.city, "Kumasi")
        self.assertEqual(client.date_of_birth, date(1990, 5, 1))

        deactivate_client(client, organization=self.org)
        client.refresh_from_db()
        self.assertEqual(client.status, ClientStatus.INACTIVE)
        self.assertEqual(
            clients_for_organization(self.org, status=ClientStatus.ACTIVE).count(),
            0,
        )

    def test_closed_client_cannot_reopen(self):
        client = create_client(organization=self.org, display_name="Close Me")
        set_client_status(client, ClientStatus.CLOSED, organization=self.org)
        with self.assertRaises(InvalidClientStatusError):
            set_client_status(client, ClientStatus.ACTIVE, organization=self.org)

    def test_update_rejects_cross_tenant(self):
        client = create_client(organization=self.org, display_name="Owned")
        with self.assertRaises(ClientNotFoundError):
            update_client(client, organization=self.other_org, phone="999")
