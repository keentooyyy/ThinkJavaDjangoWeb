import random
import string

from django.contrib import messages
from django.http.response import JsonResponse
from django.shortcuts import redirect, get_object_or_404

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section_code import SectionJoinCode
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.views.logger import create_log


def generate_code(section, department, year_level):
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    join_code, _ = SectionJoinCode.objects.update_or_create(
        section=section,
        department=department,
        year_level=year_level,
        defaults={"code": code},
    )
    return join_code.code


@session_login_required(role=Role.TEACHER)
def generate_section_code_view(request):
    teacher = request.user_obj  # ✅ validated Teacher

    if request.method != "POST":
        return redirect("register_student")

    raw = request.POST.get("section_id")

    try:
        section_id, dept_id, year_id = map(int, raw.split("_"))
    except (ValueError, AttributeError):
        messages.error(request, "Invalid section format.", extra_tags="section_codes")
        return redirect("register_student")

    handled = HandledSection.objects.filter(
        teacher=teacher,
        section_id=section_id,
        department_id=dept_id,
        year_level_id=year_id,
    ).first()

    if not handled:
        messages.error(request, "You are not assigned to this section.", extra_tags="section_codes")
        return redirect("register_student")

    code = generate_code(handled.section, handled.department, handled.year_level)

    messages.success(
        request,
        f"Code for {handled.department.name}{handled.year_level.year}{handled.section.letter}: {code}",
        extra_tags="section_codes",
    )

    create_log(
        request,
        "CREATE",
        f"Teacher {teacher.first_name} {teacher.last_name} generated join code "
        f"({code}) for section {handled.department.name}{handled.year_level.year}{handled.section.letter}."
    )
    return redirect("register_student")


@session_login_required(role=Role.TEACHER)
def delete_section_code(request):
    teacher = request.user_obj  # ✅ validated Teacher

    # 1) Prefer deleting by SectionJoinCode.id when provided
    code_id = request.POST.get("code_id")
    if code_id:
        sjc = get_object_or_404(
            SectionJoinCode.objects.select_related("section", "department", "year_level"),
            id=code_id,
        )

        authorized = HandledSection.objects.filter(
            teacher=teacher,
            section=sjc.section,
            department=sjc.department,
            year_level=sjc.year_level,
        ).exists()
        if not authorized:
            messages.error(request, "You are not assigned to this section.", extra_tags="section_codes")
            return JsonResponse({"success": False}, status=403)

        sjc.delete()
        messages.success(request, "Join code deleted successfully.", extra_tags="section_codes")

        create_log(
            request,
            "DELETE",
            f"Teacher {teacher.first_name} {teacher.last_name} deleted join code "
            f"for section {sjc.department.name}{sjc.year_level.year}{sjc.section.letter}."
        )
        return JsonResponse({"success": True})

    # 2) Fallback: composite section_id format "section_dept_year"
    raw = request.POST.get("section_id")
    try:
        section_id, dept_id, year_id = map(int, (raw or "").split("_"))
    except (ValueError, AttributeError):
        messages.error(request, "Invalid section format.", extra_tags="section_codes")
        return JsonResponse({"success": False}, status=400)

    handled = (
        HandledSection.objects
        .select_related("section", "department", "year_level")
        .filter(
            teacher=teacher,
            section_id=section_id,
            department_id=dept_id,
            year_level_id=year_id,
        )
        .first()
    )
    if not handled:
        messages.error(request, "You are not assigned to this section.", extra_tags="section_codes")
        return JsonResponse({"success": False}, status=403)

    SectionJoinCode.objects.filter(
        section=handled.section,
        department=handled.department,
        year_level=handled.year_level,
    ).delete()

    messages.success(
        request,
        f"Deleted join code for {handled.department.name}{handled.year_level.year}{handled.section.letter}.",
        extra_tags="section_codes",
    )

    create_log(
        request,
        "DELETE",
        f"Teacher {teacher.first_name} {teacher.last_name} deleted join code "
        f"for section {handled.department.name}{handled.year_level.year}{handled.section.letter}."
    )
    return JsonResponse({"success": True})
