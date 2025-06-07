from django.core.management.base import BaseCommand
from GameProgress.models.achievement_definition import AchievementDefinition

class Command(BaseCommand):
    help = "Seed default game achievements with formatted codes"

    def handle(self, *args, **kwargs):
        titles_and_descs = [
            ("First Steps", "Complete your first level."),
            ("Speedrunner", "Finish a level under 30 seconds."),
            ("Flawless Victory", "Finish without any mistakes."),
        ]

        for index, (title, description) in enumerate(titles_and_descs, start=1):
            code = f"ach_{index:03d}"  # ach_001, ach_002, etc.

            AchievementDefinition.objects.get_or_create(
                code=code,
                defaults={
                    "title": title,
                    "description": description,
                    "unlocked": False,
                }
            )

        self.stdout.write(self.style.SUCCESS("✅ Achievements seeded successfully."))
