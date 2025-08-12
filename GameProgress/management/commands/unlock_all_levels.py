from django.core.management.base import BaseCommand

from GameProgress.services.progress import unlock_all_levels


class Command(BaseCommand):
    help = "Unlock all global levels"

    def handle(self, *args, **kwargs):
        # ✅ Usage:
        # python manage.py unlock_all_levels
        # Unlocks every global level defined in LevelDefinition
        unlock_all_levels()
        self.stdout.write(self.style.SUCCESS("✅ All levels unlocked"))
