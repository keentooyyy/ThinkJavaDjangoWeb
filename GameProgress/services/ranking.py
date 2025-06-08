from GameProgress.models import LevelProgress, AchievementProgress, LevelDefinition
from StudentManagementSystem.models.student import Student


def get_student_performance(student):
    level_progress = LevelProgress.objects.filter(student=student)
    achievement_progress = AchievementProgress.objects.filter(student=student)

    total_levels = LevelDefinition.objects.count()
    max_total_time = total_levels * 180  # ⏱️ 180 seconds per level

    # 🟢 Time Attack logic: higher remaining time = better
    total_time_remaining = sum(lp.best_time for lp in level_progress)
    achievements_unlocked = achievement_progress.filter(unlocked=True).count()

    percentage_remaining = (total_time_remaining / max_total_time * 100) if max_total_time > 0 else 0

    return {
        "student_id": student.id,
        "name": student.name,

        # 🧱 Full-section (e.g. "CS3A")
        "section": getattr(student, "full_section", "N/A"),
        "department": getattr(student, "department", None).name if getattr(student, "department", None) else "N/A",
        "year_level": getattr(student, "year_level", None).year if getattr(student, "year_level", None) else "N/A",
        "section_letter": getattr(student, "section", None).letter if getattr(student, "section", None) else "N/A",

        "total_time_remaining": total_time_remaining,
        "achievements_unlocked": achievements_unlocked,
        "percentage_remaining": round(percentage_remaining, 2),
    }


def get_all_student_rankings(sort_by="time_remaining", sort_order="desc", filter_by=None, department_filter=None):
    from StudentManagementSystem.models.student import Student

    students = Student.objects.all()

    if filter_by:
        students = [s for s in students if s.full_section == filter_by]

    if department_filter:
        students = [s for s in students if s.department and s.department.name == department_filter]

    rankings = [get_student_performance(s) for s in students]

    reverse = sort_order == "desc"

    if sort_by == "time_remaining":
        rankings.sort(key=lambda r: (r["total_time_remaining"], r["achievements_unlocked"]), reverse=reverse)
    elif sort_by == "achievements":
        rankings.sort(key=lambda r: (r["achievements_unlocked"], r["total_time_remaining"]), reverse=reverse)
    elif sort_by == "percentage":
        rankings.sort(key=lambda r: r["percentage_remaining"], reverse=reverse)
    elif sort_by == "name":
        rankings.sort(key=lambda r: r["name"].lower(), reverse=reverse)
    elif sort_by == "section":
        rankings.sort(key=lambda r: (r["department"], r["year_level"], r["section_letter"]), reverse=reverse)

    return rankings
