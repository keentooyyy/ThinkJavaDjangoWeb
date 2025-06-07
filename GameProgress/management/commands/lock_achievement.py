from django.core.management.base import BaseCommand
from GameProgress.services.progress import lock_achievement

class Command(BaseCommand):
    help = "Lock a specific global achievement by code"

    def add_arguments(self, parser):
        parser.add_argument("code", type=str, help="Achievement code")

    def handle(self, *args, **options):
        # ✅ Usage:
        # python manage.py lock_achievement ach_code
        achievement = lock_achievement(options["code"])
        self.stdout.write(self.style.SUCCESS(f"🔒 Locked achievement: {achievement.code}"))
