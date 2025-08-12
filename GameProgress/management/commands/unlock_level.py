from django.core.management.base import BaseCommand

from GameProgress.services.progress import unlock_level


class Command(BaseCommand):
    help = "Unlock a specific global level"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help="Level name")

    def handle(self, *args, **options):
        # ✅ Usage:
        # python manage.py unlock_level Level6
        level = unlock_level(options["name"])
        self.stdout.write(self.style.SUCCESS(f"✅ Unlocked level: {level.name}"))
