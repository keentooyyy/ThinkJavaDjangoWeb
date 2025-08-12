from django.core.management.base import BaseCommand

from GameProgress.services.progress import enable_all_achievements


class Command(BaseCommand):
    help = "Unlock all student achievements"

    def handle(self, *args, **kwargs):
        # ✅ Usage:
        # Run this from your terminal to unlock all achievements:
        # python manage.py unlock_all_achievements
        enable_all_achievements()
        self.stdout.write(self.style.SUCCESS("✅ All achievements unlocked"))
