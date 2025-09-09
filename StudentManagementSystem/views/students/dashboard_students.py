from django.shortcuts import render, redirect

from GameProgress.models import AchievementDefinition, AchievementProgress, LevelProgress, LevelDefinition
from GameProgress.services.ranking import get_student_performance, calc_level_score, calc_level_stars
from StudentManagementSystem.models import Student


def student_dashboard(request):
    student_id = request.session.get('user_id')
    if not student_id:
        return redirect('unified_logout')

    try:
        student = Student.objects.get(id=student_id)
        first_name = student.first_name
        last_name = student.last_name

        full_name = f'{first_name} {last_name}'
    except Student.DoesNotExist:
        return redirect('unified_logout')


    achievements = get_student_achievements(student)
    performance = get_student_performance(student)
    game_completion = get_game_completion(student)
    levels = get_student_levels(student)
    context = {
        'student': student,
        'performance': performance,
        'username': full_name,
        'role': student.role,
        'achievements': achievements,
        'game_completion': game_completion,
        'levels': levels,
    }
    return render(request, 'students/dashboard.html',context )

def get_student_achievements(student):
    """Return all achievements for a student with unlocked/locked status."""

    all_achievements = AchievementDefinition.objects.all()
    progress_qs = AchievementProgress.objects.filter(student=student)

    # Create a dict: {achievement_id: unlocked_status}
    progress_map = {p.achievement_id: p.unlocked for p in progress_qs}

    achievements_status = []
    for achievement in all_achievements:
        achievements_status.append({
            "id": achievement.id,
            "title": achievement.title,
            "description": achievement.description,
            "unlocked": progress_map.get(achievement.id, False)
        })

    return achievements_status


def get_game_completion(student):
    """
    Calculate overall game progression percentage based on:
      - Levels finished (90% weight)
      - Achievements unlocked (10% weight)
    """

    # --- Levels ---
    total_levels = LevelDefinition.objects.count()
    levels_finished = (
        LevelProgress.objects.filter(student=student)
        .values("level_id")
        .distinct()
        .count()
    )
    level_progress = levels_finished / total_levels if total_levels > 0 else 0

    # --- Achievements ---
    total_achievements = AchievementDefinition.objects.count()
    unlocked_count = AchievementProgress.objects.filter(
        student=student, unlocked=True
    ).count()
    achievement_progress = (
        unlocked_count / total_achievements if total_achievements > 0 else 0
    )

    # --- Weighted completion ---
    level_score = level_progress * 80   # out of 90
    achievement_score = achievement_progress * 20   # out of 10
    completion = level_score + achievement_score

    return round(completion, 2)

def get_student_levels(student):
    progress_qs = LevelProgress.objects.filter(student=student).select_related("level")

    levels_status = []
    for lp in progress_qs:
        best_time = lp.best_time
        levels_status.append({
            "id": lp.level.id,
            "name": lp.level.name,
            "best_time": best_time,
            "score": calc_level_score(best_time),
            "stars": calc_level_stars(best_time),  # ← reusing thresholds logic
        })

    print(levels_status)
    return levels_status
