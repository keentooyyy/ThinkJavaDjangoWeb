from django.core.management.base import BaseCommand

from GameProgress.services.progress import lock_level


class Command(BaseCommand):
    help = "Lock a specific global level"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help="Level name")

    def handle(self, *args, **options):
        # ✅ Usage:
        # python manage.py lock_level Level6
        level = lock_level(options["name"])
        self.stdout.write(self.style.SUCCESS(f"✅ Locked level: {level.name}"))
