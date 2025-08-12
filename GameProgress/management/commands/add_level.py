from django.core.management.base import BaseCommand

from GameProgress.services.progress import add_level


class Command(BaseCommand):
    help = "Add a new global level (optionally unlocked)"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help="Level name")
        parser.add_argument("--unlocked", action="store_true", help="Unlock this level upon creation")

    def handle(self, *args, **options):
        # ✅ Usage:
        # Add locked level:     python manage.py add_level Level6
        # Add unlocked level:   python manage.py add_level Level6 --unlocked
        name = options["name"]
        unlocked = options["unlocked"]
        level = add_level(name, unlocked)
        self.stdout.write(self.style.SUCCESS(f"✅ Added level: {level.name} (Unlocked: {level.unlocked})"))