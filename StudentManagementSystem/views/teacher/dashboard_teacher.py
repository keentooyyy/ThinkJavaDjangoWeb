from django.shortcuts import render, redirect

from GameProgress.models import LevelDefinition, AchievementDefinition
from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Teacher
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.student import Student
from StudentManagementSystem.models.teachers import HandledSection


def get_teacher_dashboard_context(teacher):
    handled_sections = teacher.handled_sections.all()

    # Get all students (currently unfiltered)
    students = Student.objects.all()

    sections_for_department = [
        {
            "section_value": f"{hs.year_level.year}{hs.section.letter}",
            "section_display": f"{hs.year_level.year}{hs.section.letter}"
        }
        for hs in handled_sections
    ]

    full_name = f"{teacher.first_name} {teacher.last_name}"
    total_cs_section = get_total_section_by_dept("CS")
    total_it_section = get_total_section_by_dept("IT")
    top_5_students = get_teacher_top_students(teacher, limit=5)

    return {
        "teacher": teacher,
        "handled_sections": handled_sections,
        "handled_sections_names": [f"{hs.year_level.year} {hs.section.letter}" for hs in handled_sections],
        "handled_students": students,  # 🔹 can filter later to just teacher's students if needed
        "level_options": [{"value": level.name, "label": level.name} for level in LevelDefinition.objects.all()],
        "achievement_options": [
            {"value": ach.code, "label": ach.title, "is_active": ach.is_active}
            for ach in AchievementDefinition.objects.all()
        ],
        "departments": Department.objects.all(),
        "sections_for_department": sections_for_department,
        "sections": Section.objects.all(),
        "username": full_name,
        "role": Role.TEACHER,
        "total_cs_section": total_cs_section,
        "total_it_section": total_it_section,
        "top_5_students": top_5_students,
    }



@session_login_required(role=Role.TEACHER)
def teacher_dashboard(request):
    teacher = request.user_obj  # ✅ validated Teacher from decorator
    context = get_teacher_dashboard_context(teacher)
    return render(request, "teacher/dashboard.html", context)



def get_total_section_by_dept(name):
    try:
        # Example: Get IT department
        it_department = Department.objects.get(name__iexact=name)

        # Count all handled sections under IT department
        total_section = HandledSection.objects.filter(department=it_department).count()

    except Department.DoesNotExist:

        total_section = 0

    return total_section


def get_teacher_top_students(teacher, limit=5, sort_by="score", sort_order="desc"):
    """
    Return the top N students (default 5) from the sections handled by a teacher.
    Ranking is based on get_all_student_rankings.
    """

    # Get IDs of students only in the teacher's handled sections
    handled_section_ids = teacher.handled_sections.values_list("section_id", flat=True)
    student_ids = Student.objects.filter(section_id__in=handled_section_ids).values_list("id", flat=True)

    # Reuse your existing ranking function with limit_to_students
    rankings = get_all_student_rankings(
        sort_by=sort_by,
        sort_order=sort_order,
        limit_to_students=student_ids
    )

    return rankings[:limit]