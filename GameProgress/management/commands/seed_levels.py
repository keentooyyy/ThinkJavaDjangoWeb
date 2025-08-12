from django.core.management.base import BaseCommand
from GameProgress.models.level_definition import LevelDefinition

class Command(BaseCommand):
    help = "Seed Tutorial and numbered levels (Level1, Level2, ...)"

    def handle(self, *args, **kwargs):
        # ✅ Usage:
        # python manage.py seed_levels


        level_names = ["Tutorial"] + [f"Level{i}" for i in range(1, 6)]  # Customize upper range

        for name in level_names:
            LevelDefinition.objects.get_or_create(
                name=name,
                defaults={"unlocked": False}
            )

        self.stdout.write(self.style.SUCCESS("✅ Levels seeded: " + ", ".join(level_names)))
