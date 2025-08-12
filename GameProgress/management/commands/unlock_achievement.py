from django.core.management.base import BaseCommand

from GameProgress.services.progress import set_achievement_active


class Command(BaseCommand):
    help = "Unlock a specific global achievement by code"

    def add_arguments(self, parser):
        parser.add_argument("code", type=str, help="Achievement code")

    def handle(self, *args, **options):
        # ✅ Usage:
        # python manage.py unlock_achievement ach_code
        achievement = set_achievement_active(options["code"], True)
        self.stdout.write(self.style.SUCCESS(f"✅ Unlocked achievement: {achievement.code}"))
