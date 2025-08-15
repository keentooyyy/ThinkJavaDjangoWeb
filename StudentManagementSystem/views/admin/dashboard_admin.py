import json

from django.shortcuts import render, redirect

from GameProgress.services.ranking import get_section_rankings
from StudentManagementSystem.models import SimpleAdmin, Teacher, Student
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.views.admin.ranking_students import get_rankings_context


def admin_dashboard(request):
    admin_id = request.session.get('user_id')
    if not admin_id:
        return redirect('unified_login')

    admin = SimpleAdmin.objects.get(id=admin_id)
    ranking_context = get_rankings_context(request)

    # Fetch all teachers
    teachers = Teacher.objects.all()

    # Build section list grouped by department
    sections_by_department = {}
    for section in Section.objects.select_related('department', 'year_level').all():
        dept_id = section.department.id
        if dept_id not in sections_by_department:
            sections_by_department[dept_id] = []
        sections_by_department[dept_id].append({
            'id': section.id,
            'letter': section.letter
        })

    student_count_total = Student.objects.count()
    cs_id = 1
    it_id = 2
    student_count_CS = count_students(cs_id)
    student_count_IT = count_students(it_id)

    teacher_count = Teacher.objects.count()

    section_count = Section.objects.count()


    ranking_by_section = get_section_rankings()
    print(ranking_by_section)



    return render(request, 'admin/dashboard.html', {
        'admin': admin,
        'username': admin.username,
        'role': Role.ADMIN,
        'teachers': teachers,  # Pass the teachers list to the template
        'sections_by_department': json.dumps(sections_by_department),
        **ranking_context,
        'student_count': student_count_total,
        'student_count_CS': student_count_CS,
        'student_count_IT': student_count_IT,
        'teacher_count': teacher_count,
        'section_count': section_count,
        'ranking_by_section': json.dumps(ranking_by_section),

    })

def count_students(department_id=None):
    if department_id:
        # If department_id is provided, count students within that department
        return Student.objects.filter(section__department_id=department_id).count()
    # If no department_id is provided, count all students
    return Student.objects.count()
