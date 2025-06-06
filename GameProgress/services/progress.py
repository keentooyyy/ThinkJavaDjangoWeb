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
        defaults={"title": title, "description": description}
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

def lock_all_achievements():
    for ach in AchievementDefinition.objects.all():
        for progress in AchievementProgress.objects.filter(achievement=ach):
            progress.unlocked = False
            progress.save()

def unlock_all_achievements():
    for ach in AchievementDefinition.objects.all():
        for progress in AchievementProgress.objects.filter(achievement=ach):
            progress.unlocked = True
            progress.save()


def reset_all_progress():
    """Reset: Lock all levels + achievements and clear progress data."""

    # Lock all level definitions
    lock_all_levels()

    # Lock all achievement progress
    lock_all_achievements()

    # Reset each student's progress (times) per level
    for progress in LevelProgress.objects.all():
        progress.best_time = 0
        progress.current_time = 0
        progress.save()

