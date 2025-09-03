from collections import defaultdict

from django.db import models
from django.db.models import Sum, Count, Case, When, F, Q

from GameProgress.models import LevelProgress, AchievementProgress, LevelDefinition
from StudentManagementSystem.models import Student


def get_student_performance(student):
    level_progress = LevelProgress.objects.filter(student=student)
    achievement_progress = AchievementProgress.objects.filter(student=student)

    total_score = 0
    # total_levels = LevelDefinition.objects.count()
    achievements_unlocked = achievement_progress.filter(unlocked=True).count()
    # total_achievements = achievement_progress.count()
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


from django.db.models import (
    Sum, Count, Case, When, F, Q, Value, IntegerField, Subquery, OuterRef
)
from django.db.models.functions import Coalesce


def get_all_student_rankings(
    sort_by="score",
    sort_order="desc",
    filter_by=None,
    department_filter=None,
    limit_to_students=None,
):
    # Base queryset
    students = Student.objects.all()

    # Limit to specific students
    if limit_to_students is not None:
        students = students.filter(id__in=limit_to_students)

    # Filter by department
    if department_filter:
        students = students.filter(section__department__name=department_filter)

    # Filter by section like "1A", "2B"
    if filter_by:
        try:
            year = int(filter_by[0])
            section_letter = filter_by[1].upper()
            students = students.filter(
                year_level__year=year, section__letter=section_letter
            )
        except (IndexError, ValueError):
            pass

    # --- Subqueries to avoid join inflation ---

    # Level score per student
    level_score_subq = (
        LevelProgress.objects.filter(student=OuterRef("pk"))
        .annotate(
            score=Case(
                When(best_time__gte=90, then=Value(100)),
                When(best_time__gte=60, then=Value(70)),
                When(best_time__gte=30, then=Value(40)),
                When(best_time__gt=1, then=Value(10)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        .values("student")
        .annotate(total=Sum("score"))
        .values("total")[:1]
    )

    # Total time remaining
    time_subq = (
        LevelProgress.objects.filter(student=OuterRef("pk"))
        .values("student")
        .annotate(total=Sum("best_time"))
        .values("total")[:1]
    )

    # Achievements unlocked
    achievements_subq = (
        AchievementProgress.objects.filter(student=OuterRef("pk"), unlocked=True)
        .values("student")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )

    # Annotate students with subquery results
    students = (
        students.annotate(
            level_score=Coalesce(Subquery(level_score_subq, output_field=IntegerField()), Value(0)),
            total_time_remaining=Coalesce(Subquery(time_subq, output_field=IntegerField()), Value(0)),
            achievements_unlocked=Coalesce(Subquery(achievements_subq, output_field=IntegerField()), Value(0)),
        )
        .annotate(score=F("level_score") + F("achievements_unlocked") * 25)
        .select_related("section__department", "year_level")
    )

    # --- Sorting ---
    reverse = sort_order == "desc"
    if sort_by == "score":
        students = students.order_by(("-" if reverse else "") + "score")
    elif sort_by == "time_remaining":
        students = students.order_by(
            ("-" if reverse else "") + "total_time_remaining",
            ("-" if reverse else "") + "achievements_unlocked",
        )
    elif sort_by == "achievements":
        students = students.order_by(
            ("-" if reverse else "") + "achievements_unlocked",
            ("-" if reverse else "") + "total_time_remaining",
        )
    elif sort_by == "name":
        students = students.order_by(
            ("-" if reverse else "") + "last_name",
            ("-" if reverse else "") + "first_name",
        )
    elif sort_by == "section":
        students = students.order_by(
            ("-" if reverse else "") + "section__department__name",
            ("-" if reverse else "") + "year_level__year",
            ("-" if reverse else "") + "section__letter",
        )

    # --- Build result list ---
    rankings = []
    for s in students:
        rankings.append(
            {
                "student_id": s.student_id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "section": s.full_section,
                "department": (
                    s.section.department.name
                    if s.section and s.section.department
                    else "N/A"
                ),
                "year_level": s.year_level.year if s.year_level else "N/A",
                "section_letter": s.section.letter if s.section else "N/A",
                "total_time_remaining": s.total_time_remaining or 0,
                "achievements_unlocked": s.achievements_unlocked or 0,
                "score": s.score or 0,
            }
        )

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

# region old code
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
#end region code