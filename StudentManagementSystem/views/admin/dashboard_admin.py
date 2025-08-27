from django.db.models.aggregates import Count
from django.shortcuts import render, redirect

from GameProgress.models import AchievementDefinition, LevelDefinition
from GameProgress.services.ranking import get_section_rankings
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import SimpleAdmin, Teacher, Student
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section


# Function to generate the context
# @session_login_required(Role.ADMIN)
def generate_dashboard_context(admin_id):
    # Get admin details
    admin = SimpleAdmin.objects.get(id=admin_id)

    # Fetch student, teacher, and section counts in a single query (using annotate for efficiency)
    student_count_total = Student.objects.count()

    # Use annotate to get student counts for CS and IT departments in a single query
    department_counts = Section.objects.filter(department__id__in=[1, 2]).values('department__id').annotate(
        student_count=Count('student'))  # Assuming 'student' is the related name in Student model

    student_count_CS = next((count['student_count'] for count in department_counts if count['department__id'] == 1), 0)
    student_count_IT = next((count['student_count'] for count in department_counts if count['department__id'] == 2), 0)

    # Count teachers and sections with single queries
    teacher_count = Teacher.objects.count()
    section_count = Section.objects.count()

    # Build section list grouped by department with select_related for efficiency
    sections_by_department = {}
    sections = Section.objects.select_related('department', 'year_level').all()

    for section in sections:
        dept_id = section.department.id
        if dept_id not in sections_by_department:
            sections_by_department[dept_id] = []
        sections_by_department[dept_id].append({'id': section.id, 'letter': section.letter})

    # Get rankings by section
    ranking_by_section = get_section_rankings()

    # Fetch achievements and levels counts with values to avoid full object retrieval
    achievements_count = AchievementDefinition.objects.count()
    levels_count = LevelDefinition.objects.count()

    achievements_details = AchievementDefinition.objects.values('id', 'code', 'title', 'is_active')
    levels_details = LevelDefinition.objects.values('id', 'name', 'unlocked')

    # Prepare context
    context = {'username': admin.username, 'role': Role.ADMIN, 'student_count': student_count_total,
        'student_count_CS': student_count_CS, 'student_count_IT': student_count_IT, 'teacher_count': teacher_count,
        'section_count': section_count, 'ranking_by_section': ranking_by_section,
        # No need to json.dumps if it's going to be rendered directly
        'achievements_count': achievements_count, 'levels_count': levels_count,
        'achievements': list(achievements_details), 'levels': list(levels_details), }

    # Return the context to render the page
    return context


@session_login_required(Role.ADMIN)
def admin_dashboard(request):
    admin_id = request.session.get('user_id')
    if not admin_id:
        return redirect('unified_login')

    context = generate_dashboard_context(admin_id)

    return render(request, 'admin/dashboard.html', context)


@session_login_required(Role.ADMIN)
def count_students(department_id=None):
    if department_id:
        # If department_id is provided, count students within that department
        return Student.objects.filter(section__department_id=department_id).count()
    # If no department_id is provided, count all students
    return Student.objects.count()
