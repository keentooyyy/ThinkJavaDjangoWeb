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
    students = Student.objects.all()

    if limit_to_students is not None:
        students = students.filter(id__in=limit_to_students)

    if department_filter:
        students = students.filter(section__department__name=department_filter)

    if filter_by:
        try:
            year = int(filter_by[0])
            section_letter = filter_by[1].upper()
            students = students.filter(
                year_level__year=year, section__letter=section_letter
            )
        except (IndexError, ValueError):
            pass

    # level score only
    level_score_subq = (
        LevelProgress.objects.filter(student=OuterRef("pk"))
        .values("student_id", "level_id")
        .annotate(per_level_score=level_score_case("best_time"))
        .values("student_id")
        .annotate(total=Sum("per_level_score"))
        .values("total")[:1]
    )

    time_subq = (
        LevelProgress.objects.filter(student=OuterRef("pk"))
        .values("student")
        .annotate(total=Sum("best_time"))
        .values("total")[:1]
    )

    achievements_subq = (
        AchievementProgress.objects.filter(student=OuterRef("pk"), unlocked=True)
        .values("student")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )

    students = (
        students.annotate(
            level_score=Coalesce(Subquery(level_score_subq, output_field=IntegerField()), Value(0)),
            total_time_remaining=Coalesce(Subquery(time_subq, output_field=IntegerField()), Value(0)),
            achievements_unlocked=Coalesce(Subquery(achievements_subq, output_field=IntegerField()), Value(0)),
        )
        .annotate(score=F("level_score"))  # 🚫 only levels
        .select_related("section__department", "year_level")
    )

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
                "total_time_remaining": s.total_time_remaining or 0,
                "achievements_unlocked": s.achievements_unlocked or 0,
                "score": s.score or 0,
            }
        )

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

