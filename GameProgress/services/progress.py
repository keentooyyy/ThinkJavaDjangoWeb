from concurrent.futures import ThreadPoolExecutor

from django.shortcuts import get_object_or_404

from GameProgress.models import (
    LevelDefinition,
    AchievementDefinition,
    LevelProgress,
    AchievementProgress
)
from StudentManagementSystem.models.student import Student
from django.db import transaction


def sync_all_students_with_all_progress():
    students = Student.objects.values_list("id", flat=True)
    levels = list(LevelDefinition.objects.values_list("id", flat=True))
    achievements = list(AchievementDefinition.objects.values_list("id", flat=True))

    # Preload existing progress to avoid duplicates
    existing_levels = set(
        LevelProgress.objects.values_list("student_id", "level_id")
    )
    existing_achievements = set(
        AchievementProgress.objects.values_list("student_id", "achievement_id")
    )

    new_level_progress = []
    new_achievement_progress = []

    for student_id in students:
        for level_id in levels:
            key = (student_id, level_id)
            if key not in existing_levels:
                new_level_progress.append(
                    LevelProgress(student_id=student_id, level_id=level_id, best_time=0, current_time=0)
                )

        for achievement_id in achievements:
            key = (student_id, achievement_id)
            if key not in existing_achievements:
                new_achievement_progress.append(
                    AchievementProgress(student_id=student_id, achievement_id=achievement_id, unlocked=False)
                )

    # Use transactions + bulk_create in chunks
    with transaction.atomic():
        LevelProgress.objects.bulk_create(new_level_progress, batch_size=1000, ignore_conflicts=True)
        AchievementProgress.objects.bulk_create(new_achievement_progress, batch_size=1000, ignore_conflicts=True)

    print("Sync completed!")


def unlock_level(level_name):
    level = get_object_or_404(LevelDefinition, name=level_name)
    level.unlocked = True
    level.save()
    return level


def lock_level(level_name):
    level = get_object_or_404(LevelDefinition, name=level_name)
    level.unlocked = False
    level.save()
    return level


def add_level(name, unlocked=False):
    level, created = LevelDefinition.objects.get_or_create(name=name, defaults={"unlocked": unlocked})
    # if created:
    #     sync_all_students_with_all_progress()
    return level


def add_achievement(code, title, description):
    achievement, created = AchievementDefinition.objects.get_or_create(
        code=code,
        defaults={"title": title, "description": description, "is_active": True}
    )
    # if created:
    #     sync_all_students_with_all_progress()
    # return achievement


def lock_all_levels():
    for level in LevelDefinition.objects.all():
        level.unlocked = False
        level.save()


def unlock_all_levels():
    for level in LevelDefinition.objects.all():
        level.unlocked = True
        level.save()


def reset_all_progress():
    """Reset all level progress and achievement progress values."""
    lock_all_levels()

    for progress in LevelProgress.objects.all():
        progress.best_time = 0
        progress.current_time = 0
        progress.save()
    for progress in AchievementProgress.objects.all():
        progress.unlocked = False
        progress.save()


# ✅ GLOBAL ACHIEVEMENT CONTROL

def set_achievement_active(code, active=True):
    """Set whether an achievement is globally unlockable."""
    ach = get_object_or_404(AchievementDefinition, code=code)
    ach.is_active = active
    ach.save()
    return ach


def enable_all_achievements():
    """Mark all achievements as globally unlockable."""
    AchievementDefinition.objects.update(is_active=True)


def disable_all_achievements():
    """Disable all achievements from being unlockable."""
    AchievementDefinition.objects.update(is_active=False)
