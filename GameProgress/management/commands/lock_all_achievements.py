from django.core.management.base import BaseCommand
from GameProgress.services.progress import lock_all_achievements

class Command(BaseCommand):
    help = "Lock all student achievements"

    def handle(self, *args, **kwargs):
        # ✅ Usage:
        # Run this from your terminal to lock all achievements:
        # python manage.py lock_all_achievements
        lock_all_achievements()
        self.stdout.write(self.style.SUCCESS("✅ All achievements locked"))
