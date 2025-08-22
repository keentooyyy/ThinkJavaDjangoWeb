import json

from django.http.response import JsonResponse
from django.shortcuts import render, redirect

from GameProgress.models import AchievementDefinition, LevelDefinition
from GameProgress.services.ranking import get_section_rankings
from StudentManagementSystem.models import SimpleAdmin, Teacher, Student
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section




# Function to generate the context
def generate_dashboard_context(admin_id, message_container_id):
    # Get admin details
    admin = SimpleAdmin.objects.get(id=admin_id)

    # Fetch student, teacher, and section counts
    student_count_total = Student.objects.count()
    cs_id = 1
    it_id = 2
    student_count_CS = count_students(cs_id)
    student_count_IT = count_students(it_id)
    teacher_count = Teacher.objects.count()
    section_count = Section.objects.count()

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

    # Get rankings by section
    ranking_by_section = get_section_rankings()

    # Fetch achievements and levels counts
    achievements_count = AchievementDefinition.objects.count()
    levels_count = LevelDefinition.objects.count()

    achievements_details = AchievementDefinition.objects.values('code','title', 'is_active')
    levels_details = LevelDefinition.objects.values('name', 'unlocked')


    # Prepare context
    context = {
        'username': admin.username,
        'role': Role.ADMIN,
        'student_count': student_count_total,
        'student_count_CS': student_count_CS,
        'student_count_IT': student_count_IT,
        'teacher_count': teacher_count,
        'section_count': section_count,
        'ranking_by_section': json.dumps(ranking_by_section),
        'achievements_count': achievements_count,
        'levels_count': levels_count,
        'message_container_id': message_container_id,
        'achievements': list(achievements_details),
        'levels': list(levels_details),

    }

    return context


def admin_dashboard(request):
    admin_id = request.session.get('user_id')
    if not admin_id:
        return redirect('unified_login')


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
    context = generate_dashboard_context(admin_id, '')


    return render(request, 'admin/dashboard.html', context)

def count_students(department_id=None):
    if department_id:
        # If department_id is provided, count students within that department
        return Student.objects.filter(section__department_id=department_id).count()
    # If no department_id is provided, count all students
    return Student.objects.count()


