import os

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from StudentManagementSystem.models import SimpleAdmin


class Command(BaseCommand):
    help = "Seed a default admin user from .env values."

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME")
        password = os.getenv("ADMIN_PASSWORD")

        # Require username & password
        if not username or not password:
            raise CommandError(
                "❌ ADMIN_USERNAME and ADMIN_PASSWORD must be set in the .env file."
            )

        # Skip if already exists
        if SimpleAdmin.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"⚠️ Admin '{username}' already exists — skipping.")
            )
            return

        # Optional: fallback for names
        first_name = os.getenv("ADMIN_FIRST_NAME", "System")
        last_name = os.getenv("ADMIN_LAST_NAME", "Admin")

        # Create admin
        SimpleAdmin.objects.create(
            username=username,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
            role="ADMIN",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Created admin '{username}' ({first_name} {last_name}) successfully."
            )
        )
