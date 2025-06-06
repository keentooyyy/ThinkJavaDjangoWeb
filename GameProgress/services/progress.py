from django.shortcuts import get_object_or_404

from GameProgress.models import LevelDefinition, AchievementDefinition, LevelProgress, AchievementProgress


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
