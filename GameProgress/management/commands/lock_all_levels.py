from django.core.management.base import BaseCommand
from GameProgress.services.progress import lock_all_levels

class Command(BaseCommand):
    help = "Lock all global levels"

    def handle(self, *args, **kwargs):
        lock_all_levels()
        self.stdout.write(self.style.SUCCESS("✅ All levels locked"))
