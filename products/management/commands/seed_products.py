"""
Seed the product catalog with initial data.
Usage: python manage.py seed_products
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from products.models import (
    ComparisonAttribute,
    ComparisonValueType,
    PlanFeature,
    PricingPlan,
    PricingTier,
    Product,
    ProductAccent,
    ProductCategory,
    ProductComparisonEntry,
    ProductFeature,
    ProductModule,
    ProductStatus,
)


class Command(BaseCommand):
    help = "Seed product categories, products, features, pricing, and comparison data."

    @transaction.atomic
    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write(self.style.WARNING("Products already exist. Skipping seed."))
            return

        categories = {
            "vertical": ProductCategory.objects.create(
                name="Vertical Solutions",
                slug="vertical",
                description="Industry-specific SaaS products.",
                sort_order=1,
            ),
            "platform": ProductCategory.objects.create(
                name="Platform Products",
                slug="platform",
                description="Cross-industry horizontal platform modules.",
                sort_order=2,
            ),
        }

        catalog = [
            {
                "name": "ChurchHub",
                "slug": "churchhub",
                "accent": ProductAccent.CHURCHHUB,
                "category": categories["vertical"],
                "tagline": "All-in-one platform for faith communities",
                "short_description": "Manage members, giving, events, groups, and communications from a single dashboard.",
                "long_description": "ChurchHub helps faith organizations modernize operations with integrated member management, online giving, event planning, and group communications.",
                "status": ProductStatus.GA,
                "is_featured": True,
                "sort_order": 1,
                "demo_url": "https://mychurch.zreta.com/contact/",
                "register_url": "https://mychurch.zreta.com/apply/",
                "external_app_url": "https://mychurch.zreta.com/",
                "modules": ["Members", "Giving", "Events", "Communications"],
                "features": [
                    ("Member directory", "Centralized profiles, households, and engagement history."),
                    ("Online giving", "Recurring donations, campaigns, and tax receipts."),
                    ("Event management", "Registration, check-in, and volunteer scheduling."),
                ],
                "plans": [
                    ("Starter", 49, ["Up to 200 members", "Online giving", "Email support"]),
                    ("Pro", 99, ["Up to 1,000 members", "SMS & email", "Priority support"]),
                    ("Enterprise", None, ["Unlimited members", "Custom integrations", "Dedicated manager"]),
                ],
            },
            {
                "name": "Microfinance Core",
                "slug": "microfinance-core",
                "accent": ProductAccent.MICROFINANCE,
                "category": categories["vertical"],
                "tagline": "Core banking for microfinance institutions",
                "short_description": "End-to-end loan lifecycle, savings, collections, and regulatory reporting built for scale.",
                "long_description": "Microfinance Core delivers a complete banking platform for MFIs, SACCOs, and cooperatives with loan origination, disbursement, collections, and compliance reporting.",
                "status": ProductStatus.GA,
                "is_featured": False,
                "sort_order": 2,
                "modules": ["Clients", "Loans", "Savings", "Reporting"],
                "features": [
                    ("Loan management", "Full lifecycle from application to closure."),
                    ("Savings accounts", "Flexible savings products and interest calculation."),
                    ("Collections", "Automated reminders and field officer tools."),
                ],
                "plans": [
                    ("Growth", 199, ["Up to 5,000 clients", "Loan & savings modules", "Standard reports"]),
                    ("Scale", 499, ["Up to 25,000 clients", "API access", "Advanced analytics"]),
                    ("Enterprise", None, ["Unlimited clients", "Custom workflows", "On-premise option"]),
                ],
            },
            {
                "name": "ERP Suite",
                "slug": "erp-suite",
                "accent": ProductAccent.ERP,
                "category": categories["platform"],
                "tagline": "Unified operations for growing enterprises",
                "short_description": "Finance, inventory, procurement, and CRM integrated in one modular ERP platform.",
                "long_description": "ERP Suite connects finance, supply chain, procurement, and customer management into a single source of truth for operational excellence.",
                "status": ProductStatus.GA,
                "is_featured": False,
                "sort_order": 3,
                "modules": ["Finance", "Inventory", "Procurement", "CRM"],
                "features": [
                    ("General ledger", "Multi-entity, multi-currency accounting."),
                    ("Inventory control", "Real-time stock across warehouses."),
                    ("Procurement", "Purchase orders, approvals, and vendor management."),
                ],
                "plans": [
                    ("Business", 149, ["5 users", "Finance & inventory", "Email support"]),
                    ("Professional", 349, ["25 users", "All modules", "Phone support"]),
                    ("Enterprise", None, ["Unlimited users", "Custom modules", "SLA guarantee"]),
                ],
            },
            {
                "name": "School Management",
                "slug": "school-management",
                "accent": ProductAccent.SCHOOL,
                "category": categories["vertical"],
                "tagline": "Modern administration for educational institutions",
                "short_description": "Admissions, academics, fees, attendance, and parent engagement — streamlined.",
                "long_description": "School Management simplifies academic and administrative workflows for K-12 and higher-ed institutions with integrated admissions, grading, and fee collection.",
                "status": ProductStatus.GA,
                "is_featured": False,
                "sort_order": 4,
                "modules": ["Admissions", "Academics", "Fees", "Parent Portal"],
                "features": [
                    ("Admissions pipeline", "Online applications and enrollment workflows."),
                    ("Fee management", "Invoicing, payment tracking, and reminders."),
                    ("Parent portal", "Grades, attendance, and communication."),
                ],
                "plans": [
                    ("Academy", 79, ["Up to 500 students", "Core modules", "Email support"]),
                    ("Campus", 179, ["Up to 2,000 students", "Parent portal", "Priority support"]),
                    ("District", None, ["Unlimited students", "Multi-campus", "Dedicated support"]),
                ],
            },
            {
                "name": "Hospital Management",
                "slug": "hospital-management",
                "accent": ProductAccent.HOSPITAL,
                "category": categories["vertical"],
                "tagline": "Healthcare operations, simplified",
                "short_description": "Appointments, billing, pharmacy, lab, and patient records in a compliant platform.",
                "long_description": "Hospital Management streamlines clinical and administrative workflows for hospitals and clinics with EMR-lite, billing, pharmacy, and lab integrations.",
                "status": ProductStatus.GA,
                "is_featured": False,
                "sort_order": 5,
                "modules": ["Appointments", "Billing", "Pharmacy", "Laboratory"],
                "features": [
                    ("Patient records", "Secure, searchable patient history."),
                    ("Appointment scheduling", "Multi-provider calendars and reminders."),
                    ("Billing & claims", "Insurance integration and invoicing."),
                ],
                "plans": [
                    ("Clinic", 129, ["Up to 10 providers", "Appointments & billing", "Standard support"]),
                    ("Hospital", 399, ["Up to 50 providers", "All modules", "Priority support"]),
                    ("Health System", None, ["Unlimited providers", "HL7/FHIR integration", "Dedicated CSM"]),
                ],
            },
            {
                "name": "HR & Payroll",
                "slug": "hr-payroll",
                "accent": ProductAccent.HR,
                "category": categories["platform"],
                "tagline": "People operations for modern organizations",
                "short_description": "Employee records, payroll processing, leave, recruitment, and performance in one system.",
                "long_description": "HR & Payroll automates people operations from hire to retire with compliant payroll, leave management, and performance reviews.",
                "status": ProductStatus.GA,
                "is_featured": False,
                "sort_order": 6,
                "modules": ["Employee Records", "Payroll", "Leave", "Recruitment"],
                "features": [
                    ("Payroll automation", "Multi-country tax rules and direct deposit."),
                    ("Leave management", "Policies, approvals, and accrual tracking."),
                    ("Recruitment", "Job postings, applicant tracking, and onboarding."),
                ],
                "plans": [
                    ("Team", 59, ["Up to 50 employees", "Core HR & payroll", "Email support"]),
                    ("Business", 129, ["Up to 250 employees", "Recruitment module", "Phone support"]),
                    ("Enterprise", None, ["Unlimited employees", "Custom workflows", "Dedicated HR advisor"]),
                ],
            },
            {
                "name": "Retail Commerce",
                "slug": "retail-commerce",
                "accent": ProductAccent.DEFAULT,
                "category": categories["vertical"],
                "tagline": "Omnichannel retail management — launching soon",
                "short_description": "Point of sale, inventory, and e-commerce unified for modern retailers.",
                "long_description": "Retail Commerce will bring POS, inventory sync, and online storefront management into one platform. Join the waitlist to get early access.",
                "status": ProductStatus.COMING_SOON,
                "is_featured": False,
                "sort_order": 7,
                "modules": [],
                "features": [],
                "plans": [],
            },
        ]

        comparison_attrs = [
            ("Mobile app", "Core", ComparisonValueType.BOOLEAN),
            ("API access", "Core", ComparisonValueType.BOOLEAN),
            ("Multi-currency", "Core", ComparisonValueType.BOOLEAN),
            ("24/7 support", "Support", ComparisonValueType.BOOLEAN),
            ("Custom integrations", "Enterprise", ComparisonValueType.BOOLEAN),
            ("On-premise deployment", "Enterprise", ComparisonValueType.BOOLEAN),
        ]

        attributes = {}
        for i, (name, group, vtype) in enumerate(comparison_attrs):
            attributes[name] = ComparisonAttribute.objects.create(
                name=name, group=group, value_type=vtype, sort_order=i + 1
            )

        for item in catalog:
            product = Product.objects.create(
                name=item["name"],
                slug=item["slug"],
                accent=item["accent"],
                category=item["category"],
                tagline=item["tagline"],
                short_description=item["short_description"],
                long_description=item["long_description"],
                status=item["status"],
                is_featured=item.get("is_featured", False),
                is_published=True,
                sort_order=item["sort_order"],
                demo_url=item.get("demo_url", ""),
                register_url=item.get("register_url", ""),
                external_app_url=item.get("external_app_url", ""),
            )

            for i, mod_name in enumerate(item.get("modules", [])):
                ProductModule.objects.create(
                    product=product, name=mod_name, sort_order=i + 1
                )

            for i, (title, desc) in enumerate(item.get("features", [])):
                ProductFeature.objects.create(
                    product=product,
                    title=title,
                    description=desc,
                    sort_order=i + 1,
                    is_highlighted=i == 0,
                )

            for i, (plan_name, price, bullets) in enumerate(item.get("plans", [])):
                plan = PricingPlan.objects.create(
                    product=product,
                    name=plan_name,
                    slug=plan_name.lower().replace(" ", "-"),
                    is_popular=(i == 1),
                    is_contact_sales=(price is None),
                    sort_order=i + 1,
                )
                if price is not None:
                    PricingTier.objects.create(
                        plan=plan, currency="USD", region="global", amount=Decimal(str(price))
                    )
                for j, text in enumerate(bullets):
                    PlanFeature.objects.create(plan=plan, text=text, sort_order=j + 1)

            if product.status == ProductStatus.GA:
                ProductComparisonEntry.objects.create(
                    product=product, attribute=attributes["Mobile app"], value_boolean=True
                )
                ProductComparisonEntry.objects.create(
                    product=product, attribute=attributes["API access"],
                    value_boolean=(product.slug in {"erp-suite", "microfinance-core"}),
                )
                ProductComparisonEntry.objects.create(
                    product=product, attribute=attributes["Multi-currency"], value_boolean=True
                )
                ProductComparisonEntry.objects.create(
                    product=product, attribute=attributes["24/7 support"],
                    value_boolean=(product.slug != "churchhub"),
                )
                ProductComparisonEntry.objects.create(
                    product=product, attribute=attributes["Custom integrations"],
                    value_boolean=(product.slug in {"erp-suite", "hospital-management"}),
                )
                ProductComparisonEntry.objects.create(
                    product=product, attribute=attributes["On-premise deployment"],
                    value_boolean=(product.slug in {"microfinance-core", "hospital-management"}),
                )

        self.stdout.write(self.style.SUCCESS(f"Seeded {Product.objects.count()} products."))
