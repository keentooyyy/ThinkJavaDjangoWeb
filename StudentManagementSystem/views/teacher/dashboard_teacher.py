from django.shortcuts import render, redirect

from GameProgress.models import LevelDefinition, AchievementDefinition
from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.models import Teacher
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.student import Student
from StudentManagementSystem.views.admin.ranking_students import get_rankings_context


def get_teacher_dashboard_context(teacher):
    handled_sections = teacher.handled_sections.select_related('department', 'year_level', 'section')

    # print(f"Handled sections: {handled_sections}")
    # print(f"Handled sections count: {handled_sections.count()}")

    # Get all students (no filters applied for now)
    students = Student.objects.all()

    # Get the rankings for the filtered students
    rankings = get_all_student_rankings(sort_by="score", sort_order="desc")

    # Only get the sections that the teacher is handling
    sections_for_department = [
        {
            'section_value': f"{hs.year_level.year}{hs.section.letter}",
            'section_display': f"{hs.year_level.year} {hs.section.letter}"
        }
        for hs in handled_sections
    ]


    return {
        'teacher': teacher,
        'rankings': rankings,
        'handled_sections': handled_sections,
        'handled_sections_names': [
            f"{hs.year_level.year} {hs.section.letter}" for hs in handled_sections
        ],
        'handled_students': students,  # Current handled students for the teacher (no filter)
        'level_options': [
            {"value": level.name, "label": level.name}
            for level in LevelDefinition.objects.all()
        ],
        'achievement_options': [
            {
                "value": ach.code,
                "label": ach.title,
                "is_active": ach.is_active
            }
            for ach in AchievementDefinition.objects.all()
        ],
        'departments': Department.objects.all(),
        'sections_for_department': sections_for_department,  # Only sections relevant to the selected department
        'sections': Section.objects.all(),
    }


def teacher_dashboard(request):
    teacher_id = request.session.get('user_id')
    if not teacher_id:
        return redirect('unified_login')

    teacher = Teacher.objects.get(id=teacher_id)

    # Get static + relational UI data
    context = get_teacher_dashboard_context(teacher)

    # Get dynamic ranking data
    ranking_context = get_rankings_context(request, teacher=teacher)

    # Merge both
    context.update(ranking_context)

    return render(request, 'teacher/dashboard.html', context)
