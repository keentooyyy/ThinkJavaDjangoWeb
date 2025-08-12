from django.core.management.base import BaseCommand

from GameProgress.services.progress import add_achievement


class Command(BaseCommand):
    help = "Add a new global achievement"

    def add_arguments(self, parser):
        parser.add_argument("code", type=str, help="Achievement code")
        parser.add_argument("title", type=str, help="Achievement title")
        parser.add_argument("description", type=str, help="Achievement description")

    def handle(self, *args, **options):
        # ✅ Usage:
        # python manage.py add_achievement ach_010 "Master Coder" "Completed Level 6 fast"
        ach = add_achievement(options["code"], options["title"], options["description"])
        self.stdout.write(self.style.SUCCESS(f"✅ Added achievement: {ach.code} - {ach.title}"))
