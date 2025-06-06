from django.core.management.base import BaseCommand
from GameProgress.services.progress import sync_all_students_with_all_progress

class Command(BaseCommand):
    help = "Sync all students with global levels and achievements"

    def handle(self, *args, **kwargs):
        # ✅ Usage: python manage.py sync_progress
        # Ensures all students have LevelProgress and AchievementProgress entries
        sync_all_students_with_all_progress()
        self.stdout.write(self.style.SUCCESS("✅ Synced all students with global progress"))
