from django.http.response import JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden

from GameProgress.services.ranking import get_all_student_rankings
# from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import SimpleAdmin, Student
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section

# @session_login_required(Role.ADMIN)
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
        return {}  # If the user is neither an admin nor a teacher, return an empty dictionary


# @session_login_required(Role.ADMIN)
def student_ranking(request):
    # Check for admin role
    user_context = get_user_context(request)
    role = user_context.get('role')
    if role != Role.ADMIN:
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get parameters from GET request
    department_name = request.GET.get("department")
    section_filter = request.GET.get("filter_by")
    sort_by = request.GET.get("sort_by", "")
    sort_order = request.GET.get("sort_order", "")
    page_number = request.GET.get("page", 1)
    per_page = int(request.GET.get("per_page", 25))

    # Get departments
    departments = Department.objects.all().order_by("name")

    # Get sections for admin (admin sees all sections, filtered by department)
    if department_name and department_name.lower() != "all":
        sections = Section.objects.filter(department__name=department_name) \
            .select_related("year_level").order_by("year_level__year", "letter")
    else:
        sections = Section.objects.select_related("year_level").order_by("year_level__year", "letter")

    # Manually filter unique sections based on year and letter (ignoring department)
    unique_sections = []
    for section in sections:
        section_key = f"{section.year_level.year}{section.letter}"  # Concatenate year and letter

        # Check if section (year + letter) is already in the list (ignoring department)
        if not any(f"{s.year_level.year}{s.letter}" == section_key for s in unique_sections):
            unique_sections.append(section)

    # Get the rankings based on the filtering
    rankings = get_all_student_rankings(
        sort_by=sort_by,
        sort_order=sort_order,
        filter_by=section_filter,
        department_filter=None if department_name and department_name.lower() == "all" else department_name
    )

    # Pagination
    paginator = Paginator(rankings, per_page)
    page_obj = paginator.get_page(page_number)

    # Render the student_ranking.html template with context
    context = {
        'departments': departments,
        'sections': unique_sections,  # Only show unique sections handled by the teacher
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

