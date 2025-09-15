from django.shortcuts import render

from GameProgress.models import AchievementDefinition, AchievementProgress, LevelProgress, LevelDefinition
from GameProgress.services.ranking import get_student_performance, calc_level_score, calc_level_stars
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models.roles import Role


@session_login_required(role=Role.STUDENT)
def student_dashboard(request):
    student = request.user_obj  # ✅ DB-validated Student from decorator
    full_name = f"{student.first_name} {student.last_name}"

    achievements = get_student_achievements(student)
    performance = get_student_performance(student)
    game_completion = get_game_completion(student)
    levels = get_student_levels(student)

    context = {
        "student": student,
        "performance": performance,
        "username": full_name,
        "role": student.role,
        "achievements": achievements,
        "game_completion": game_completion,
        "levels": levels,
    }
    return render(request, "students/main/dashboard.html", context)

def get_student_achievements(student):
    """Return all achievements for a student with unlocked/locked status."""
    all_achievements = AchievementDefinition.objects.all()
    progress_qs = AchievementProgress.objects.filter(student=student)
    progress_map = {p.achievement_id: p.unlocked for p in progress_qs}

    return [
        {
            "id": achievement.id,
            "title": achievement.title,
            "description": achievement.description,
            "unlocked": progress_map.get(achievement.id, False),
        }
        for achievement in all_achievements
    ]

def get_game_completion(student):
    """
    Calculate overall game progression percentage based on:
      - Levels finished (90% weight)
      - Achievements unlocked (10% weight)
    """
    total_levels = LevelDefinition.objects.count()
    levels_finished = (
        LevelProgress.objects.filter(student=student, best_time__gt=0)
        .values("level_id")
        .distinct()
        .count()
    )
    level_progress = levels_finished / total_levels if total_levels > 0 else 0

    total_achievements = AchievementDefinition.objects.count()
    unlocked_count = AchievementProgress.objects.filter(student=student, unlocked=True).count()
    achievement_progress = unlocked_count / total_achievements if total_achievements > 0 else 0

    level_score = level_progress * 90
    achievement_score = achievement_progress * 10

    if levels_finished == 0:  # optional rule
        achievement_score = 0

    return round(level_score + achievement_score, 2)

def get_student_levels(student):
    progress_qs = LevelProgress.objects.filter(student=student).select_related("level")

    return [
        {
            "id": lp.level.id,
            "name": lp.level.name,
            "best_time": lp.best_time,
            "score": calc_level_score(lp.best_time),
            "stars": calc_level_stars(lp.best_time),
        }
        for lp in progress_qs
    ]
