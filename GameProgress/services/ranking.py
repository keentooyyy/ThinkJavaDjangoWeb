from GameProgress.models import LevelProgress, AchievementProgress, LevelDefinition
from StudentManagementSystem.models.student import Student


def get_student_performance(student):
    level_progress = LevelProgress.objects.filter(student=student)
    achievement_progress = AchievementProgress.objects.filter(student=student)

    total_score = 0
    total_levels = LevelDefinition.objects.count()
    achievements_unlocked = achievement_progress.filter(unlocked=True).count()
    total_achievements = achievement_progress.count()
    total_time_remaining = 0

    for lp in level_progress:
        remaining = lp.best_time
        total_time_remaining += remaining

        # 🧠 Stricter Time Attack Scoring
        if remaining >= 90:
            total_score += 100
        elif remaining >= 60:
            total_score += 70
        elif remaining >= 30:
            total_score += 40
        elif remaining > 1:
            total_score += 10
        else:
            total_score += 0  # Failed or not completed

    # 🎯 Tighter Achievement Bonus
    achievement_bonus = achievements_unlocked * 25
    total_score += achievement_bonus

    return {
        "student_id": student.id,
        "name": student.name,
        "section": getattr(student, "full_section", "N/A"),
        "department": getattr(student.section, "department", None).name if getattr(student.section, "department", None) else "N/A",
        "year_level": getattr(student, "year_level", None).year if getattr(student, "year_level", None) else "N/A",
        "section_letter": getattr(student, "section", None).letter if getattr(student, "section", None) else "N/A",
        "total_time_remaining": total_time_remaining,
        "achievements_unlocked": achievements_unlocked,
        "score": total_score
    }


def get_all_student_rankings(sort_by="score", sort_order="desc", filter_by=None, department_filter=None, limit_to_students=None):
    # Base queryset
    students = Student.objects.all()

    # Optional limit to a predefined set of student IDs (e.g., teacher's students)
    if limit_to_students is not None:
        students = students.filter(id__in=limit_to_students)

    # Filter by department
    if department_filter:
        students = students.filter(section__department__name=department_filter)

    # Filter by section in format '1A', '2B', etc.
    if filter_by:
        try:
            year = int(filter_by[0])
            section_letter = filter_by[1].upper()
            students = students.filter(year_level__year=year, section__letter=section_letter)
        except (IndexError, ValueError):
            pass  # Ignore invalid filter input

    # Compute performance per student
    rankings = [get_student_performance(s) for s in students]

    # Sort by selected criteria
    reverse = sort_order == "desc"

    if sort_by == "score":
        rankings.sort(key=lambda r: r["score"], reverse=reverse)
    elif sort_by == "time_remaining":
        rankings.sort(key=lambda r: (r["total_time_remaining"], r["achievements_unlocked"]), reverse=reverse)
    elif sort_by == "achievements":
        rankings.sort(key=lambda r: (r["achievements_unlocked"], r["total_time_remaining"]), reverse=reverse)
    elif sort_by == "name":
        rankings.sort(key=lambda r: r["name"].lower(), reverse=reverse)
    elif sort_by == "section":
        rankings.sort(key=lambda r: (r["department"], r["year_level"], r["section_letter"]), reverse=reverse)

    return rankings
