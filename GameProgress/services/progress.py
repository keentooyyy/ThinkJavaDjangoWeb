from django.shortcuts import get_object_or_404
from GameProgress.models import (
    LevelDefinition,
    AchievementDefinition,
    LevelProgress,
    AchievementProgress
)
from StudentManagementSystem.models.student import Student


def sync_all_students_with_all_progress():
    students = Student.objects.all()
    levels = LevelDefinition.objects.all()
    achievements = AchievementDefinition.objects.all()

    for student in students:
        for level in levels:
            LevelProgress.objects.get_or_create(student=student, level=level)
        for ach in achievements:
            AchievementProgress.objects.get_or_create(student=student, achievement=ach)


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
    if created:
        sync_all_students_with_all_progress()
    return level


def add_achievement(code, title, description):
    achievement, created = AchievementDefinition.objects.get_or_create(
        code=code,
        defaults={"title": title, "description": description, "is_active": True}
    )
    if created:
        sync_all_students_with_all_progress()
    return achievement


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
