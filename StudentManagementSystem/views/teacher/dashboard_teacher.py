from django.shortcuts import render, redirect
from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.models import Teacher
from StudentManagementSystem.models.department import Department


def teacher_dashboard(request):
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('teacher_login')

    teacher = Teacher.objects.get(id=teacher_id)
    rankings = get_all_student_rankings(sort_by="percentage", sort_order="desc")

    # Get all assignments
    handled_sections = teacher.handled_sections.select_related('department', 'year_level', 'section')

    section_info = [
        f"{hs.department.name}{hs.year_level.year}{hs.section.letter}"
        for hs in handled_sections
    ]

    return render(request, 'teacher/dashboard.html', {
        'teacher': teacher,
        'rankings': rankings,
        'sections_handled': section_info,
    })
