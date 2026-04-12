"""
Management command: python manage.py seed_data

Creates sample users and complaints so the app can be demoed immediately.

Sample credentials
------------------
  Admin   ->  username: admin       password: Admin@123
  Citizen ->  username: alice       password: Alice@123
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from complaints.models import Complaint, Notification


SAMPLE_COMPLAINTS = [
    {
        "title": "Large pothole on MG Road",
        "desc": "There is a dangerous pothole on MG Road near the junction. Several bikes have been damaged.",
        "location": "MG Road, Chennai",
        "latitude": 13.0604,
        "longitude": 80.2496,
        "status": "pending",
        "category": "road",
    },
    {
        "title": "Burst water pipe near Park Ave",
        "desc": "A water pipe has been leaking near Park Avenue for three days. The road is flooded.",
        "location": "Park Avenue, Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "status": "inprogress",
        "category": "water",
    },
    {
        "title": "Garbage not collected for a week",
        "desc": "Garbage from our street has not been collected. Trash and waste are piling up.",
        "location": "Anna Nagar, Chennai",
        "latitude": 13.0878,
        "longitude": 80.2102,
        "status": "resolved",
        "category": "sanitation",
    },
    {
        "title": "Broken street light",
        "desc": "The street light at the corner has been broken for two weeks. It is unsafe at night.",
        "location": "T Nagar, Chennai",
        "latitude": 13.0418,
        "longitude": 80.2341,
        "status": "pending",
        "category": "general",
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample admin, citizen, and complaint data"

    def handle(self, *args, **kwargs):
        # ── Admin ──────────────────────────────────────────
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@smartcivic.com",
                password="Admin@123",
            )
            self.stdout.write(self.style.SUCCESS("Created admin  ->  admin / Admin@123"))
        else:
            self.stdout.write("Admin user already exists, skipping.")

        # ── Citizen ────────────────────────────────────────
        if not User.objects.filter(username="alice").exists():
            citizen = User.objects.create_user(
                username="alice",
                email="alice@example.com",
                password="Alice@123",
            )
            self.stdout.write(self.style.SUCCESS("Created citizen ->  alice / Alice@123"))
        else:
            citizen = User.objects.get(username="alice")
            self.stdout.write("Citizen 'alice' already exists, skipping creation.")

        # ── Complaints ─────────────────────────────────────
        if Complaint.objects.filter(user=citizen).count() == 0:
            for data in SAMPLE_COMPLAINTS:
                Complaint.objects.create(user=citizen, **data)
            self.stdout.write(self.style.SUCCESS(f"Created {len(SAMPLE_COMPLAINTS)} sample complaints for alice."))

            # Notification for the resolved complaint
            resolved = Complaint.objects.filter(user=citizen, status='resolved').first()
            if resolved:
                Notification.objects.create(
                    user=citizen,
                    message=f"{resolved.title} -> resolved"
                )
        else:
            self.stdout.write("Complaints already exist for alice, skipping.")

        self.stdout.write(self.style.SUCCESS("\nDone! You can now log in at http://127.0.0.1:8000/"))
        self.stdout.write("  Admin   ->  /adminlogin/   username: admin   password: Admin@123")
        self.stdout.write("  Citizen ->  /userlogin/    username: alice   password: Alice@123")
