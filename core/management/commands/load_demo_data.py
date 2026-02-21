# core/management/commands/load_demo_data.py

"""
Management command to load rich demo data for presentations and development.

Usage:
    python manage.py load_demo_data            # Load demo data (safe to re-run)
    python manage.py load_demo_data --reset    # Wipe all estate data and reload fresh

Login credentials after running:
    Email:    demo@estate.com
    Password: demo1234
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import random
from datetime import timedelta

from accounts.models import User
from estates.models import Estate
from units.models import Unit
from payments.models import Fee, FeeAssignment, Payment
from maintenance.models import MaintenanceTicket
from announcements.models import Announcement


class Command(BaseCommand):
    help = "Load rich demo data for presentations and development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing demo data before loading fresh records.",
        )

    def handle(self, *args, **kwargs):
        reset = kwargs["reset"]

        if reset:
            self.stdout.write(self.style.WARNING("⚠  --reset flag detected. Wiping demo estate data..."))
            self._reset_demo_data()

        self.stdout.write(self.style.WARNING("🔄  Loading demo data..."))

        with transaction.atomic():
            manager = self._create_manager()
            estate = self._create_estate(manager)
            units = self._create_units(estate, manager)
            fees = self._create_fees(estate, manager)
            self._create_payments(fees, units, manager)
            self._create_maintenance_tickets(estate, manager, units)
            self._create_announcements(estate, manager)

        self._print_summary(estate, units, fees)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def _reset_demo_data(self):
        """Remove all data tied to the demo estate for a clean reload."""
        deleted_count, _ = Estate.objects.filter(name="Greenview Estate").delete()
        User.objects.filter(email="demo@estate.com").delete()
        if deleted_count:
            self.stdout.write(self.style.SUCCESS("  ✓ Demo data wiped."))
        else:
            self.stdout.write("  (No existing demo data found — nothing to wipe.)")

    # ------------------------------------------------------------------
    # 1. Manager account
    # ------------------------------------------------------------------

    def _create_manager(self):
        """
        Get or create the demo estate manager account.

        Uses create_user() to ensure the password is correctly hashed.
        This is intentionally a weak password for demo purposes only —
        never use demo credentials in a production environment.
        """
        manager = User.objects.filter(email="demo@estate.com").first()

        if not manager:
            manager = User.objects.create_user(
                email="demo@estate.com",
                password="demo1234",
                first_name="Demo",
                last_name="Manager",
                role=User.Role.ESTATE_MANAGER,
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS("  ✓ Demo manager account created."))
        else:
            self.stdout.write("  · Demo manager already exists — skipping.")

        return manager

    # ------------------------------------------------------------------
    # 2. Estate
    # ------------------------------------------------------------------

    def _create_estate(self, manager):
        """Create the demo estate if it does not already exist."""
        estate, created = Estate.objects.get_or_create(
            name="Greenview Estate",
            defaults={
                "estate_type": "PRIVATE",
                "approximate_units": 20,
                "fee_frequency": "YEARLY",
                "is_active": True,
                "manager": manager,
            },
        )

        label = "created" if created else "already exists — skipping"
        self.stdout.write(self.style.SUCCESS(f"  ✓ Estate '{estate.name}' {label}."))
        return estate

    # ------------------------------------------------------------------
    # 3. Units
    # ------------------------------------------------------------------

    # Deterministic seed so re-runs without --reset produce consistent data.
    _OCCUPIED_UNITS = {1, 2, 3, 5, 6, 8, 9, 10}   # 8 out of 12 occupied

    _RESIDENT_NAMES = [
        "Adebayo Okafor",
        "Chisom Eze",
        "Fatima Al-Hassan",
        "Emeka Nwosu",
        "Ngozi Adeleke",
        "Tunde Balogun",
        "Amaka Obi",
        "Yusuf Musa",
    ]

    def _create_units(self, estate, manager):
        """
        Create 12 residential units with realistic Nigerian resident data.

        Units 4, 7, 11, and 12 are intentionally left vacant to demonstrate
        the unoccupied state in the UI.
        """
        units = []
        resident_pool = list(self._RESIDENT_NAMES)

        for i in range(1, 13):
            occupied = i in self._OCCUPIED_UNITS

            defaults = {
                "owner": manager,
                "is_occupied": occupied,
            }

            if occupied and resident_pool:
                name = resident_pool.pop(0)
                # Phone numbers follow the Nigerian +234 format with valid
                # prefixes (0802 / 0803 / 0806 / 0813) to satisfy regex validators.
                prefix = random.choice(["0802", "0803", "0806", "0813"])
                phone = f"+234{prefix[1:]}{random.randint(1000000, 9999999)}"
                defaults.update({
                    "occupant_name": name,
                    "occupant_phone": phone,
                })

            unit, created = Unit.objects.get_or_create(
                estate=estate,
                identifier=f"House {i}",
                defaults=defaults,
            )
            units.append(unit)

        occupied_count = sum(1 for u in units if u.is_occupied)
        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ {len(units)} units ready "
                f"({occupied_count} occupied, {len(units) - occupied_count} vacant)."
            )
        )
        return units

    # ------------------------------------------------------------------
    # 4. Fees
    # ------------------------------------------------------------------

    _FEES = [
        {
            "name": "Security Levy 2025",
            "amount": Decimal("20000.00"),
            "description": (
                "Annual security levy covering 24/7 guard services, CCTV "
                "maintenance, and perimeter lighting for the 2025 fiscal year."
            ),
            "due_offset_days": 30,
        },
        {
            "name": "Estate Maintenance Charge 2025",
            "amount": Decimal("15000.00"),
            "description": (
                "Covers landscaping, road maintenance, drainage clearing, "
                "and general upkeep of communal areas for 2025."
            ),
            "due_offset_days": 60,
        },
        {
            "name": "Water Infrastructure Levy 2025",
            "amount": Decimal("10000.00"),
            "description": (
                "Funds borehole servicing, overhead tank maintenance, "
                "and emergency water supply for 2025."
            ),
            "due_offset_days": 45,
        },
    ]

    def _create_fees(self, estate, manager):
        """Create multiple fees with realistic descriptions and staggered due dates."""
        today = timezone.now().date()
        created_fees = []

        for fee_data in self._FEES:
            due_date = today + timedelta(days=fee_data["due_offset_days"])
            fee, created = Fee.objects.get_or_create(
                estate=estate,
                name=fee_data["name"],
                defaults={
                    "amount": fee_data["amount"],
                    "description": fee_data["description"],
                    "due_date": due_date,
                    "created_by": manager,
                },
            )
            created_fees.append(fee)

        self.stdout.write(self.style.SUCCESS(f"  ✓ {len(created_fees)} fees ready."))
        return created_fees

    # ------------------------------------------------------------------
    # 5. Payments (via FeeAssignment)
    # ------------------------------------------------------------------

    # Deterministic payment matrix: set of (fee_index, unit_identifier) pairs
    # that should be marked as paid. Keeps demo data consistent across re-runs.
    _PAID_ASSIGNMENTS = {
        # Security Levy — 7 of 12 paid
        (0, "House 1"), (0, "House 2"), (0, "House 3"),
        (0, "House 5"), (0, "House 6"), (0, "House 8"), (0, "House 9"),
        # Estate Maintenance — 5 of 12 paid
        (1, "House 1"), (1, "House 2"), (1, "House 5"),
        (1, "House 8"), (1, "House 10"),
        # Water Levy — 3 of 12 paid
        (2, "House 2"), (2, "House 6"), (2, "House 9"),
    }

    def _create_payments(self, fees, units, manager):
        """
        Create FeeAssignment records for every fee/unit combination, then
        record Payment objects for the predetermined paid assignments.

        The FeeAssignment + Payment separation mirrors the production payment
        flow:  assign fee → resident pays → manager records payment.
        """
        assignment_count = 0
        payment_count = 0

        for fee_index, fee in enumerate(fees):
            for unit in units:
                is_paid = (fee_index, unit.identifier) in self._PAID_ASSIGNMENTS

                assignment, a_created = FeeAssignment.objects.get_or_create(
                    fee=fee,
                    unit=unit,
                    defaults={
                        "status": FeeAssignment.PaymentStatus.PAID if is_paid else FeeAssignment.PaymentStatus.UNPAID,
                    },
                )

                if a_created:
                    assignment_count += 1

                # Only create a Payment record for paid assignments.
                if is_paid and not hasattr(assignment, "payment"):
                    Payment.objects.get_or_create(
                        fee_assignment=assignment,
                        defaults={
                            "amount": fee.amount,
                            "payment_method": random.choice([
                                Payment.PaymentMethod.CASH,
                                Payment.PaymentMethod.BANK_TRANSFER,
                            ]),
                            "payment_date": timezone.now() - timedelta(days=random.randint(1, 20)),
                            "recorded_by": manager,
                            "notes": "Recorded at estate office.",
                        },
                    )
                    payment_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ {assignment_count} fee assignments created, "
                f"{payment_count} payments recorded."
            )
        )

    # ------------------------------------------------------------------
    # 6. Maintenance tickets
    # ------------------------------------------------------------------

    _TICKETS = [
        {
            "title": "No water supply in Block A",
            "description": (
                "Residents in Houses 1–4 reported a complete loss of water "
                "supply as of Monday morning. The overhead tank appears empty "
                "and the borehole pump may have tripped. Immediate inspection required."
            ),
            "category": MaintenanceTicket.CategoryChoices.WATER,
            "status": MaintenanceTicket.StatusChoices.OPEN,
            "unit_identifier": "House 1",
        },
        {
            "title": "Street light at main entrance not working",
            "description": (
                "The sodium-vapour street lamp at the main gate has been off "
                "for three consecutive nights. Residents have raised safety "
                "concerns. The lamp post and ballast need to be inspected."
            ),
            "category": MaintenanceTicket.CategoryChoices.ELECTRICITY,
            "status": MaintenanceTicket.StatusChoices.RESOLVED,
            "unit_identifier": None,
        },
        {
            "title": "Blocked drainage channel near House 7",
            "description": (
                "Heavy rainfall last week caused the storm drain alongside "
                "House 7 to overflow onto the road. The channel is blocked "
                "with debris and needs clearing before the next rainy season."
            ),
            "category": MaintenanceTicket.CategoryChoices.WASTE,
            "status": MaintenanceTicket.StatusChoices.OPEN,
            "unit_identifier": "House 7",
        },
        {
            "title": "Broken perimeter fence — rear wall",
            "description": (
                "A section of the rear perimeter wall (approximately 3 metres) "
                "collapsed following soil erosion. Security risk — the gap "
                "allows unauthorised access from the adjoining property."
            ),
            "category": MaintenanceTicket.CategoryChoices.SECURITY,
            "status": MaintenanceTicket.StatusChoices.OPEN,
            "unit_identifier": None,
        },
        {
            "title": "Generator exhaust pipe causing smoke nuisance",
            "description": (
                "The communal generator exhaust near the estate office is "
                "directing fumes toward House 10. Residents have complained "
                "of headaches. The exhaust pipe needs to be re-routed upwards."
            ),
            "category": MaintenanceTicket.CategoryChoices.OTHER,
            "status": MaintenanceTicket.StatusChoices.OPEN,
            "unit_identifier": "House 10",
        },
    ]

    def _create_maintenance_tickets(self, estate, manager, units):
        """
        Create a varied set of maintenance tickets covering multiple categories
        and statuses to give a realistic picture in the dashboard.
        """
        unit_map = {u.identifier: u for u in units}
        created_count = 0

        for ticket_data in self._TICKETS:
            unit = unit_map.get(ticket_data["unit_identifier"])

            _, created = MaintenanceTicket.objects.get_or_create(
                estate=estate,
                title=ticket_data["title"],
                defaults={
                    "description": ticket_data["description"],
                    "category": ticket_data["category"],
                    "status": ticket_data["status"],
                    "created_by": manager,
                    "unit": unit,
                    "resolved_at": (
                        timezone.now() - timedelta(days=5)
                        if ticket_data["status"] == MaintenanceTicket.StatusChoices.RESOLVED
                        else None
                    ),
                },
            )

            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✓ {created_count} maintenance tickets created."))

    # ------------------------------------------------------------------
    # 7. Announcements
    # ------------------------------------------------------------------

    _ANNOUNCEMENTS = [
        {
            "title": "Monthly Security Meeting — Saturday 5 PM",
            "message": (
                "Dear residents,\n\n"
                "There will be a mandatory estate security meeting this Saturday "
                "at 5:00 PM in the community hall. Agenda items include the broken "
                "perimeter fence, new visitor registration procedures, and the "
                "proposed installation of an additional security camera at the rear gate.\n\n"
                "All household representatives are expected to attend.\n\n"
                "— Demo Manager, Greenview Estate"
            ),
        },
        {
            "title": "Water Supply Outage — Wednesday 8 AM to 2 PM",
            "message": (
                "Dear residents,\n\n"
                "Please be informed that the estate water supply will be interrupted "
                "this Wednesday from 8:00 AM to approximately 2:00 PM due to scheduled "
                "borehole servicing and pump maintenance.\n\n"
                "Kindly store sufficient water before the outage begins. We apologise "
                "for any inconvenience.\n\n"
                "— Demo Manager, Greenview Estate"
            ),
        },
        {
            "title": "Reminder: 2025 Security Levy Now Due",
            "message": (
                "Dear residents,\n\n"
                "This is a reminder that the 2025 Security Levy of ₦20,000 is now "
                "due. Payment can be made at the estate office (cash) or via bank "
                "transfer — please collect account details from the office.\n\n"
                "Kindly ensure payment is made before the due date to avoid disruption "
                "to estate services.\n\n"
                "— Demo Manager, Greenview Estate"
            ),
        },
    ]

    def _create_announcements(self, estate, manager):
        """Create realistic announcements that reflect active estate operations."""
        created_count = 0

        for ann_data in self._ANNOUNCEMENTS:
            _, created = Announcement.objects.get_or_create(
                estate=estate,
                title=ann_data["title"],
                defaults={
                    "message": ann_data["message"],
                    "created_by": manager,
                    "is_active": True,
                },
            )

            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✓ {created_count} announcements created."))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _print_summary(self, estate, units, fees):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 55))
        self.stdout.write(self.style.SUCCESS("  ✅  Demo data loaded successfully!"))
        self.stdout.write(self.style.SUCCESS("=" * 55))
        self.stdout.write(f"  Estate  : {estate.name}")
        self.stdout.write(f"  Units   : {len(units)} (run with --reset to regenerate)")
        self.stdout.write(f"  Fees    : {len(fees)}")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("  Login credentials (demo only — not for production):"))
        self.stdout.write(f"    Email   : demo@estate.com")
        self.stdout.write(f"    Password: demo1234")
        self.stdout.write(self.style.SUCCESS("=" * 55))
        self.stdout.write("")