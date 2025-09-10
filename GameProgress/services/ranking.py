import re
from collections import defaultdict

from django.db import models
from django.db.models import Sum, Count, Case, When, F, Q
from django.db.models import (
    Sum, Count, Case, When, F, Q, Value, IntegerField, Subquery, OuterRef
)
from django.db.models.functions import Coalesce

from GameProgress.models import LevelProgress, AchievementProgress, LevelDefinition
from StudentManagementSystem.models import Student


LEVEL_SCORE_THRESHOLDS = [
    (90, 100),
    (60, 70),
    (30, 40),
    (1, 10),
]


def calc_level_stars(best_time: int) -> int:
    """Stars are derived from the score value using thresholds (reuse)."""
    score = calc_level_score(best_time)

    for threshold, s in LEVEL_SCORE_THRESHOLDS:
        if score == s:
            # map position in the list to stars
            # top entry in list → 3 stars, then 2, then 2, then 1
            idx = LEVEL_SCORE_THRESHOLDS.index((threshold, s))
            stars_map = {0: 3, 1: 2, 2: 2, 3: 1}
            return stars_map[idx]
    return 0

def calc_level_score(best_time: int) -> int:
    """Python-side scoring for a single level."""
    if best_time is None:
        return 0
    for threshold, score in LEVEL_SCORE_THRESHOLDS:
        if best_time >= threshold:
            return score
    return 0

def level_score_case(field="best_time"):
    """Reusable ORM scoring expression."""
    whens = [When(**{f"{field}__gte": t}, then=Value(s)) for t, s in LEVEL_SCORE_THRESHOLDS]
    return Case(*whens, default=Value(0), output_field=IntegerField())

# --------------------------
# Student performance (single)
# --------------------------
def get_student_performance(student):
    # Aggregate per level
    level_progress = (
        LevelProgress.objects.filter(student=student)
        .values("level_id")
        .annotate(best_time=models.Max("best_time"))
    )

    total_score = 0
    total_time_remaining = 0

    for lp in level_progress:
        remaining = lp["best_time"]
        total_time_remaining += remaining
        total_score += calc_level_score(remaining)

    achievements_unlocked = AchievementProgress.objects.filter(student=student, unlocked=True).count()

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
        "score": total_score,  # 🚫 no +25 per achievement
    }

# --------------------------
# All student rankings
# --------------------------
def get_all_student_rankings(
    sort_by="score",
    sort_order="desc",
    filter_by=None,
    department_filter=None,
    limit_to_students=None,
):
    # --- Precompute scores like get_section_rankings ---
    level_scores = (
        LevelProgress.objects
        .values("student_id", "level_id")
        .annotate(per_level_score=level_score_case("best_time"))
        .values("student_id")
        .annotate(level_score=Sum("per_level_score"))
    )
    level_map = {row["student_id"]: row["level_score"] or 0 for row in level_scores}

    time_scores = (
        LevelProgress.objects
        .values("student_id")
        .annotate(total_time=Sum("best_time"))
    )
    time_map = {row["student_id"]: row["total_time"] or 0 for row in time_scores}

    achievement_scores = (
        AchievementProgress.objects.filter(unlocked=True)
        .values("student_id")
        .annotate(total=Count("id"))
    )
    achievement_map = {row["student_id"]: row["total"] or 0 for row in achievement_scores}

    # --- Base queryset: all students ---
    students = Student.objects.select_related("section__department", "year_level").all()

    # --- Filters ---
    if limit_to_students is not None:
        students = students.filter(id__in=limit_to_students)

    if department_filter:
        students = students.filter(section__department__name=department_filter)

    if filter_by:
        match = re.match(r"([A-Za-z]*)(\d+)([A-Za-z])", filter_by)
        if match:
            dept, year, section_letter = match.groups()
            filters = {
                "year_level__year": int(year),
                "section__letter": section_letter.upper(),
            }
            if dept:
                filters["section__department__name"] = dept.upper()
            students = students.filter(**filters)

    print("Filter by:", filter_by)
    print("Department filter:", department_filter)
    print("Student IDs limit:", list(limit_to_students)[:20] if limit_to_students else "None")
    print("Does Kentoy exist in Student DB?", Student.objects.filter(student_id="17-2168-338").exists())
    print("Kentoy details:", Student.objects.filter(student_id="17-2168-338").values(
        "id", "student_id", "year_level__year", "section__letter", "section__department__name"
    ))
    # --- Build rankings ---
    rankings = []
    for s in students:
        rankings.append(
            {
                "student_id": s.student_id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "section": s.full_section,
                "department": s.section.department.name if s.section and s.section.department else "N/A",
                "year_level": s.year_level.year if s.year_level else "N/A",
                "section_letter": s.section.letter if s.section else "N/A",
                "total_time_remaining": time_map.get(s.id, 0),
                "achievements_unlocked": achievement_map.get(s.id, 0),
                "score": level_map.get(s.id, 0),
            }
        )

    print(f"Rankings: {rankings}")
    # --- Sorting ---
    reverse = sort_order == "desc"
    if sort_by == "score":
        rankings.sort(key=lambda r: r["score"], reverse=reverse)
    elif sort_by == "time_remaining":
        rankings.sort(key=lambda r: (r["total_time_remaining"], r["achievements_unlocked"]), reverse=reverse)
    elif sort_by == "achievements":
        rankings.sort(key=lambda r: (r["achievements_unlocked"], r["total_time_remaining"]), reverse=reverse)
    elif sort_by == "name":
        rankings.sort(key=lambda r: (r["last_name"], r["first_name"]), reverse=reverse)
    elif sort_by == "section":
        rankings.sort(key=lambda r: (r["department"], r["year_level"], r["section_letter"]), reverse=reverse)

    return rankings

# --------------------------
# Section rankings
# --------------------------
def get_section_rankings(sort_order="desc", limit=5):
    # per student level scores
    level_scores = (
        LevelProgress.objects
        .values("student_id", "level_id")
        .annotate(per_level_score=level_score_case("best_time"))
        .values("student_id")
        .annotate(level_score=Sum("per_level_score"))
    )
    level_map = {row["student_id"]: row["level_score"] or 0 for row in level_scores}

    students = Student.objects.select_related("section__department", "section__year_level").all()

    section_groups = {}
    for s in students:
        total_score = level_map.get(s.id, 0)  # 🚫 no achievement bonus

        if s.section:
            section_name = f"{s.section.department.name}{s.section.year_level.year}{s.section.letter}"
            section_groups.setdefault(section_name, []).append(total_score)

    section_averages = [
        {"section": sec, "average_score": sum(scores) / len(scores) if scores else 0}
        for sec, scores in section_groups.items()
    ]

    reverse = sort_order == "desc"
    section_averages.sort(key=lambda x: x["average_score"], reverse=reverse)

    return section_averages[:limit]

