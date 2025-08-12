from django.core.management.base import BaseCommand

from GameProgress.models.achievement_definition import AchievementDefinition


class Command(BaseCommand):
    help = "Seed default game achievements with formatted codes"

    def handle(self, *args, **kwargs):
        # ✅ Usage:
        # python manage.py seed_achievements
        titles_and_descs = [
            ("First Steps", "Complete your first level."),
            ("Speedrunner", "Finish a level under 30 seconds."),
            ("Flawless Victory", "Finish without any mistakes."),
        ]

        for index, (title, description) in enumerate(titles_and_descs, start=1):
            code = f"ach_{index:03d}"  # ach_001, ach_002, etc.

            # Removed the 'unlocked' field from the defaults dictionary
            AchievementDefinition.objects.get_or_create(
                code=code,
                defaults={
                    "title": title,
                    "description": description,
                    "is_active": True,  # Ensure 'is_active' is set to True (or leave it as default)
                }
            )

        self.stdout.write(self.style.SUCCESS("✅ Achievements seeded successfully."))
