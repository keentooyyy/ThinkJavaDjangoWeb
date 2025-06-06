from django.core.management.base import BaseCommand
from GameProgress.services.progress import reset_all_progress

class Command(BaseCommand):
    help = "Reset all level and achievement progress (lock everything)"

    def handle(self, *args, **kwargs):
        # ✅ Usage:
        # Run this from your terminal to lock ALL levels and achievements for testing:
        # python manage.py reset_all_progress
        reset_all_progress()
        self.stdout.write(self.style.SUCCESS("✅ All progress reset: levels and achievements locked"))
