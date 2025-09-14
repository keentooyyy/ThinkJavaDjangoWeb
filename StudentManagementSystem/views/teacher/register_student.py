from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db.models.query_utils import Q
from django.http.response import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Student, SectionJoinCode
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection, Teacher
from StudentManagementSystem.views.logger import create_log
from StudentManagementSystem.views.ranking_view import build_ranking_context, paginate_queryset, get_common_params, \
    deduplicate_sections
from StudentManagementSystem.views.sync_all_progress import run_sync_in_background


@session_login_required(role=Role.TEACHER)
def register_student(request):
    """ GET → show students list with filters
        POST → create a new student
    """
    extra_tags = "create_message"
    teacher = request.user_obj  # ✅ validated Teacher

    # ✅ Handle student creation
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        section_id = request.POST.get("section_id")  # actual PK from form
        password = request.POST.get("password")

        if not first_name or not last_name or not section_id or not password:
            messages.error(request, "All fields are required.", extra_tags=extra_tags)
            return redirect("register_student")

        # Make sure the section belongs to this teacher
        handled_section = (
            HandledSection.objects
            .filter(teacher=teacher, section_id=section_id)
            .select_related("section")
            .first()
        )

        if not handled_section:
            messages.error(request, "You are not assigned to this section.", extra_tags=extra_tags)
            return redirect("register_student")

        # Create student with hashed password
        student = Student.objects.create(
            first_name=first_name,
            last_name=last_name,
            section=handled_section.section,
            year_level=handled_section.section.year_level,
            student_id=student_id,
            password=make_password(password),  # ✅ securely hashed
        )
        run_sync_in_background()

        messages.success(
            request,
            f"Student {student.first_name} {student.last_name} registered successfully.",
            extra_tags=extra_tags,
        )

        create_log(
            request,
            "CREATE",
            f"Teacher {teacher.first_name} {teacher.last_name} registered a new student "
            f"{student.first_name} {student.last_name} ({student.student_id}) "
            f"in section {handled_section.section.department.name}"
            f"{handled_section.section.year_level.year}{handled_section.section.letter}."
        )
        return redirect("register_student")

    handled_sections = HandledSection.objects.filter(teacher=teacher)
    if not handled_sections.exists():
        messages.error(request, "You are not assigned to any sections yet.", extra_tags=extra_tags)

    # available sections for dropdown
    unique_sections = deduplicate_sections([hs.section for hs in handled_sections])

    departments = Department.objects.all()
    if not departments.exists():
        messages.error(request, "No departments available.", extra_tags=extra_tags)

    section_codes = SectionJoinCode.objects.filter(section__in=[hs.section for hs in handled_sections])

    params = get_common_params(request)

    students = Student.objects.filter(
        section__in=handled_sections.values_list("section_id", flat=True)
    ).select_related("section__department", "year_level")

    if params["department_name"] and params["department_name"].lower() != "all":
        students = students.filter(section__department__name=params["department_name"])
    if params["section_filter"]:
        year = params["section_filter"][:1]
        letter = params["section_filter"][1:]
        students = students.filter(section__year_level__year=year, section__letter=letter)

    search_query = request.GET.get("search", "").strip().lower()
    if search_query:
        students = students.filter(
            Q(student_id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(section__letter__icontains=search_query) |
            Q(section__year_level__year__icontains=search_query)
        )

    students = students.order_by("student_id")

    page_obj = paginate_queryset(students, params["per_page"], params["page_number"])

    context = build_ranking_context(
        students,
        page_obj,
        params,
        {"username": f"{teacher.first_name} {teacher.last_name}", "role": Role.TEACHER},
        {
            "departments": departments,
            "sections": unique_sections,
            "selected_department": params["department_name"],
            "selected_section": params["section_filter"],
            "section_codes": section_codes,
            "handled_sections": handled_sections,
        },
    )

    return render(request, "teacher/main/register_student.html", context)


# ----------------------------
# Edit Student
# ----------------------------
@session_login_required(role=Role.TEACHER)
def edit_student(request, student_id):
    teacher = request.user_obj  # ✅ validated Teacher
    student = get_object_or_404(Student, id=student_id)

    handled_sections = (
        HandledSection.objects
        .filter(teacher=teacher)
        .select_related("section__year_level", "department")
        .order_by("department__name", "section__year_level__year", "section__letter")
    )

    if not handled_sections.filter(section=student.section).exists():
        return JsonResponse({"success": False, "message": "Not authorized"}, status=403)

    if request.method == "GET":
        departments_dict = {}
        for hs in handled_sections:
            dept_id = hs.department.id
            if dept_id not in departments_dict:
                departments_dict[dept_id] = {
                    "id": dept_id,
                    "name": hs.department.name,
                    "sections": []
                }
            departments_dict[dept_id]["sections"].append({
                "id": hs.section.id,
                "year": hs.section.year_level.year,
                "letter": hs.section.letter
            })

        return JsonResponse({
            "success": True,
            "student": {
                "id": student.id,
                "student_id": student.student_id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "department_id": student.section.department.id,
                "department_name": student.section.department.name,
                "section_id": student.section.id,
                "section_display": f"{student.section.department.name}"
                                   f"{student.section.year_level.year}"
                                   f"{student.section.letter}",
            },
            "departments": list(departments_dict.values())
        })

    if request.method == "POST":
        old_first_name = student.first_name
        old_last_name = student.last_name
        old_password = student.password
        old_section = student.section

        first_name = request.POST.get("student_first_name_modal")
        last_name = request.POST.get("student_last_name_modal")
        section_id = request.POST.get("student_section_modal")
        raw_password = request.POST.get("student_password_modal")

        if not first_name or not last_name or not section_id:
            messages.error(request, "All fields are required.", extra_tags="edit_message")
            return JsonResponse({"success": False})

        try:
            new_section = Section.objects.select_related("department", "year_level").get(id=section_id)
        except Section.DoesNotExist:
            messages.error(request, "Invalid section selected.", extra_tags="edit_message")
            return JsonResponse({"success": False})

        if not handled_sections.filter(section=new_section).exists():
            messages.error(request, "You are not authorized to assign this section.", extra_tags="edit_message")
            return JsonResponse({"success": False})

        changes = []
        if first_name and first_name != old_first_name:
            changes.append(f"first name from '{old_first_name}' to '{first_name}'")
            student.first_name = first_name
        if last_name and last_name != old_last_name:
            changes.append(f"last name from '{old_last_name}' to '{last_name}'")
            student.last_name = last_name
        if new_section != old_section:
            changes.append(
                f"section from '{old_section.department.name}{old_section.year_level.year}{old_section.letter}' "
                f"to '{new_section.department.name}{new_section.year_level.year}{new_section.letter}'"
            )
            student.section = new_section
            student.year_level = new_section.year_level
        if raw_password:
            hashed_password = make_password(raw_password)
            if hashed_password != old_password:
                changes.append("password updated")
                student.password = hashed_password

        student.save()

        if changes:
            log_description = (
                f"Teacher {teacher.first_name} {teacher.last_name} updated "
                f"{', '.join(changes)} for student ({student.student_id}) "
                f"named {student.first_name} {student.last_name}."
            )
            create_log(request, "UPDATE", log_description)

        messages.success(
            request,
            f"Student {student.first_name} {student.last_name} updated successfully!",
            extra_tags="edit_message"
        )
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "message": "Invalid method"}, status=405)


# ----------------------------
# Delete Student
# ----------------------------
@session_login_required(role=Role.TEACHER)
def delete_student(request, student_id):
    teacher = request.user_obj  # ✅ validated Teacher
    student = get_object_or_404(Student, id=student_id)

    handled_sections = HandledSection.objects.filter(teacher=teacher).values_list("section_id", flat=True)
    if student.section_id not in handled_sections:
        messages.error(request, "You are not authorized to delete this student.", extra_tags="edit_message")
        return JsonResponse({"success": False}, status=403)

    if request.method in ["DELETE", "POST"]:
        student_name = f"{student.first_name} {student.last_name}"
        student_id_val = student.student_id
        section_name = f"{student.section.department.name}{student.section.year_level.year}{student.section.letter}"

        log_description = (
            f"Teacher {teacher.first_name} {teacher.last_name} deleted student "
            f"({student_id_val}) named {student_name} from section {section_name}."
        )

        student.delete()
        messages.success(request, f"Student {student_name} deleted successfully.", extra_tags="edit_message")
        create_log(request, "DELETE", log_description)

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

