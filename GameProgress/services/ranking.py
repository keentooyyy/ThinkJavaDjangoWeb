from collections import defaultdict

from django.db import models
from django.db.models import Sum, Count, Case, When, F, Q

from GameProgress.models import LevelProgress, AchievementProgress, LevelDefinition
from StudentManagementSystem.models import Student


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
        "student_id": student.student_id,
        "first_name": student.first_name,
        "last_name": student.last_name,
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


def get_section_rankings(sort_order="desc", limit=5):
    """
    Compute top-N sections by average student score.
    Avoids join multiplication by separating level and achievement queries.
    """

    # --- Level scores per student ---
    level_scores = (
        LevelProgress.objects
        .values("student_id")
        .annotate(
            level_score=Sum(
                Case(
                    When(best_time__gte=90, then=100),
                    When(best_time__gte=60, then=70),
                    When(best_time__gte=30, then=40),
                    When(best_time__gt=1, then=10),
                    default=0,
                    output_field=models.IntegerField(),
                )
            )
        )
    )
    level_map = {row["student_id"]: row["level_score"] or 0 for row in level_scores}

    # --- Achievement scores per student ---
    ach_scores = (
        AchievementProgress.objects
        .filter(unlocked=True)
        .values("student_id")
        .annotate(ach_score=Count("id") * 25)
    )
    ach_map = {row["student_id"]: row["ach_score"] or 0 for row in ach_scores}

    # --- Combine per student ---
    students = Student.objects.select_related("section__department", "year_level").all()

    section_groups = {}
    for s in students:
        total_score = level_map.get(s.id, 0) + ach_map.get(s.id, 0)
        if s.section:
            section_name = f"{s.section.department.name}{s.year_level.year}{s.section.letter}"
            section_groups.setdefault(section_name, []).append(total_score)

    # --- Average per section ---
    section_averages = [
        {"section": sec, "average_score": sum(scores) / len(scores) if scores else 0}
        for sec, scores in section_groups.items()
    ]

    # --- Sort and limit ---
    reverse = sort_order == "desc"
    section_averages.sort(key=lambda x: x["average_score"], reverse=reverse)

    return section_averages[:limit]


# Ranking Based on Sections
# def get_section_rankings(sort_order="desc", limit=5):
#     # Base queryset for students
#     students = Student.objects.all()
#
#     # Group students by their full section
#     section_groups = defaultdict(list)
#
#     for student in students:
#         # Get the full section for each student
#         full_section = getattr(student, "full_section", "N/A")
#
#         # Calculate the student's performance and score
#         student_performance = get_student_performance(student)
#         student_score = student_performance["score"]
#
#         # Add the student and their score to the appropriate section group
#         section_groups[full_section].append(student_score)
#
#     # Calculate the average score for each section
#     section_averages = []
#     for section, scores in section_groups.items():
#         average_score = sum(scores) / len(scores) if scores else 0
#         section_averages.append({
#             "section": section,
#             "average_score": average_score
#         })
#
#     # Sort sections by average score
#     reverse = sort_order == "desc"
#     section_averages.sort(key=lambda x: x["average_score"], reverse=reverse)
#
#     # Return the top N sections based on average score
#     return section_averages[:limit]