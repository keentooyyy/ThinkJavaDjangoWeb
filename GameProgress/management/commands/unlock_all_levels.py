from django.core.management.base import BaseCommand
from GameProgress.services.progress import unlock_all_levels

class Command(BaseCommand):
    help = "Unlock all global levels"

    def handle(self, *args, **kwargs):
        unlock_all_levels()
        self.stdout.write(self.style.SUCCESS("✅ All levels unlocked"))
