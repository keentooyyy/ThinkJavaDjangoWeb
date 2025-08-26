from django.http.response import JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden

from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import SimpleAdmin, Student, Teacher
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section


def get_user_context(request):
    """Helper function to get the role and username of the current user."""
    user_id = request.session.get('user_id')  # Fetch the user ID from the session
    try:
        # Check if the user is an admin
        admin = SimpleAdmin.objects.get(id=user_id)
        return {
            'username': admin.username,
            'role': admin.role,  # Role for SimpleAdmin (Admin)
        }
    except SimpleAdmin.DoesNotExist:
        try:
            # If not an admin, check if the user is a teacher
            teacher = Teacher.objects.get(id=user_id)
            return {
                'username': teacher.first_name,  # Optionally, you can use full name
                'role': teacher.role,  # Role for Teacher
            }
        except Teacher.DoesNotExist:
            return {}  # If the user is neither an admin nor a teacher, return an empty dictionary

@session_login_required(Role.ADMIN)
def student_ranking(request):
    # Check for admin or teacher roles
    user_context = get_user_context(request)
    role = user_context.get('role')
    if role not in [Role.ADMIN, Role.TEACHER]:
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get parameters from GET request
    department_name = request.GET.get("department")
    section_filter = request.GET.get("filter_by")
    sort_by = request.GET.get("sort_by", "")
    sort_order = request.GET.get("sort_order", "")
    page_number = request.GET.get("page", 1)
    per_page = int(request.GET.get("per_page", 25))

    departments = Department.objects.all().order_by("name")
    limit_to_students = None

    # Handle teacher-specific logic or show all sections for admin
    if role == Role.TEACHER:
        # Get the sections handled by the teacher
        handled_sections = user_context.get('teacher').handled_sections.select_related("year_level", "section", "department")

        all_handled_section_ids = [hs.section.id for hs in handled_sections]

        # Filter the sections based on the department if a department is specified
        if department_name and department_name.lower() != "all":
            filtered_section_ids = [
                hs.section.id for hs in handled_sections if hs.department.name == department_name
            ]
        else:
            filtered_section_ids = all_handled_section_ids

        # Query the sections for the teacher's handled sections only
        sections = Section.objects.filter(id__in=filtered_section_ids).select_related('year_level') \
            .order_by('year_level__year', 'letter')

        # Limit the students to those in the handled sections
        limit_to_students = Student.objects.filter(
            section__id__in=filtered_section_ids
        ).values_list('id', flat=True)

    else:
        # For admin role, show all sections
        if department_name and department_name.lower() != "all":
            sections = Section.objects.filter(department__name=department_name) \
                .select_related("year_level").order_by("year_level__year", "letter")
        else:
            sections = Section.objects.select_related("year_level").order_by("year_level__year", "letter")

    unique_sections = []
    seen = set()
    for section in sections:
        section_key = (section.year_level.id, section.letter)
        if section_key not in seen:
            seen.add(section_key)
            unique_sections.append(section)

    sections = unique_sections

    # Get the rankings based on the filtering
    rankings = get_all_student_rankings(
        sort_by=sort_by,
        sort_order=sort_order,
        filter_by=section_filter,
        department_filter=None if department_name and department_name.lower() == "all" else department_name,
        limit_to_students=limit_to_students
    )

    paginator = Paginator(rankings, per_page)
    page_obj = paginator.get_page(page_number)

    # Render the student_ranking.html template with context
    context = {
        'departments': departments,
        'sections': sections,
        'rankings': page_obj.object_list,
        'page_obj': page_obj,
        'selected_department': department_name,
        'selected_section': section_filter,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'per_page': per_page,
        'username': user_context['username'],
        'role': user_context['role'],
    }

    return render(request, 'admin/student_ranking.html', context)


