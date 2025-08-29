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


# @session_login_required(Role.TEACHER)
def get_teacher_dashboard_context(request, teacher):
    # teacher = Teacher.objects.get(id=request.session.get('user_id'))
    handled_sections = teacher.handled_sections.all()
    # print(handled_sections)

    # Get all students (no filters applied for now)
    students = Student.objects.all()

    # ranking_context = student_ranking(request, True, teacher)
    # print(ranking_context.content.decode('utf-8'))
    #
    # Only get the sections that the teacher is handling
    sections_for_department = [{'section_value': f"{hs.year_level.year}{hs.section.letter}",
                                'section_display': f"{hs.year_level.year}{hs.section.letter}"} for hs in
                               handled_sections]
    full_name = teacher.first_name + " " + teacher.last_name
    total_cs_section = get_total_section_by_dept("CS")
    total_it_section = get_total_section_by_dept("IT")

    top_5_students = get_teacher_top_students(teacher, limit=5)
    # Combine everything into the context
    return {'teacher': teacher,  # Ensure rankings is available
            'handled_sections': handled_sections,
            'handled_sections_names': [f"{hs.year_level.year} {hs.section.letter}" for hs in handled_sections],
            'handled_students': students,  # Current handled students for the teacher (no filter)
            'level_options': [{"value": level.name, "label": level.name} for level in LevelDefinition.objects.all()],
            'achievement_options': [{"value": ach.code, "label": ach.title, "is_active": ach.is_active} for ach in
                                    AchievementDefinition.objects.all()], 'departments': Department.objects.all(),
            'sections_for_department': sections_for_department,  # Only sections relevant to the selected department
            'sections': Section.objects.all(), 'username': full_name, 'role': Role.TEACHER,
            'total_cs_section': total_cs_section, 'total_it_section': total_it_section, 'top_5_students': top_5_students,}


@session_login_required(role=Role.TEACHER)
def teacher_dashboard(request):
    teacher_id = request.session.get('user_id')
    if not teacher_id:
        return redirect('unified_login')

    teacher = Teacher.objects.get(id=teacher_id)
    # Get static + relational UI data
    context = get_teacher_dashboard_context(request, teacher)

    return render(request, 'teacher/dashboard.html', context)


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