from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import render

from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Teacher, Student
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection


@session_login_required(role=Role.TEACHER)
def get_teacher_context(request):
    """Helper function to get the role and full name of the current teacher."""
    user_id = request.session.get("user_id")  # user_id should map to Teacher
    try:
        teacher = Teacher.objects.get(id=user_id)
        full_name = f"{teacher.first_name} {teacher.last_name}"
        return {"username": full_name, "role": teacher.role}  # 👈 keep key as 'username'
    except Teacher.DoesNotExist:
        return {}




@session_login_required(role=Role.TEACHER)
def student_ranking_teacher(request):
    user_context = get_teacher_context(request)
    if user_context.get("role") != Role.TEACHER:
        return HttpResponseForbidden("You do not have permission to access this page.")

    teacher_id = request.session.get("user_id")

    # Get parameters
    department_name = request.GET.get("department")
    section_filter = request.GET.get("filter_by")
    sort_by = request.GET.get("sort_by", "")
    sort_order = request.GET.get("sort_order", "")
    page_number = request.GET.get("page", 1)
    per_page = int(request.GET.get("per_page", 25))

    # 🔹 all handled sections (no filtering, for department list)
    all_handled_sections = (
        HandledSection.objects.filter(teacher_id=teacher_id)
        .select_related("section__year_level", "department")
        .order_by("department__name", "section__year_level__year", "section__letter")
    )

    # 🔹 filtered handled sections (for rankings + sections list)
    handled_sections = all_handled_sections
    if department_name and department_name.lower() != "all":
        handled_sections = handled_sections.filter(department__name=department_name)

    # Extract unique sections (ignore duplicate year+letter across departments)
    unique_sections = []
    for hs in handled_sections:
        section = hs.section
        section_key = f"{section.year_level.year}{section.letter}"
        if not any(f"{s.section.year_level.year}{s.section.letter}" == section_key for s in unique_sections):
            unique_sections.append(hs)

    # Collect all student IDs in filtered sections
    student_ids = (
        Student.objects.filter(section__in=handled_sections.values_list("section_id", flat=True))
        .values_list("id", flat=True)
    )

    # Rankings (restricted to teacher’s students only)
    rankings = get_all_student_rankings(
        sort_by=sort_by,
        sort_order=sort_order,
        filter_by=section_filter,
        department_filter=None if department_name and department_name.lower() == "all" else department_name,
        limit_to_students=student_ids,
    )

    # Pagination
    paginator = Paginator(rankings, per_page)
    page_obj = paginator.get_page(page_number)

    # Context
    context = {
        # 🔹 always show all teacher-handled departments in dropdown
        "departments": Department.objects.filter(
            id__in=all_handled_sections.values_list("department_id", flat=True).distinct()
        ).order_by("name"),
        "sections": [hs.section for hs in unique_sections],
        "rankings": page_obj.object_list,
        "page_obj": page_obj,
        "selected_department": department_name,
        "selected_section": section_filter,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "per_page": per_page,
        "username": user_context["username"],
        "role": user_context["role"],
    }

    return render(request, "admin/student_ranking.html", context)

