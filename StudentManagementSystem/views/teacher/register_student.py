from django.contrib import messages
from django.core.paginator import Paginator
from django.http.response import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Student, SectionJoinCode
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection, Teacher


def get_students_for_teacher(teacher_id, department=None, section=None, sort_by=None, sort_order=None, per_page=25):
    handled_sections = HandledSection.objects.filter(teacher_id=teacher_id)
    students = Student.objects.filter(section__in=[hs.section for hs in handled_sections])

    if department:
        students = students.filter(section__department__name=department)

    if section:
        year = section[:1]
        letter = section[1:]
        students = students.filter(section__year_level__year=year, section__letter=letter)

    if sort_by:
        students = students.order_by(f"{'-' if sort_order == 'desc' else ''}{sort_by}")
    else:
        students = students.order_by("student_id")

    return Paginator(students, per_page)


@session_login_required(role=Role.TEACHER)
def register_student(request):
    """
    GET  → show students list with filters
    POST → create a new student
    """
    extra_tags = "create_message"
    teacher_id = request.session.get("user_id")

    if not teacher_id:
        messages.error(request, "Unauthorized access. Please log in first.", extra_tags=extra_tags)
        return redirect("unified_logout")

    # ✅ Handle student creation
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        section_id = request.POST.get("section_id")  # actual PK from form

        if not first_name or not last_name or not section_id:
            messages.error(request, "All fields are required.", extra_tags=extra_tags)
            return redirect("register_student")

        # Make sure the section belongs to this teacher
        handled_section = HandledSection.objects.filter(
            teacher_id=teacher_id,
            section_id=section_id,
        ).select_related("section").first()

        if not handled_section:
            messages.error(request, "You are not assigned to this section.", extra_tags=extra_tags)
            return redirect("register_student")

        # Create student
        student = Student.objects.create(
            first_name=first_name,
            last_name=last_name,
            section=handled_section.section,
            student_id=student_id,
        )

        messages.success(
            request,
            f"Student {student.first_name} {student.last_name} registered successfully.",
            extra_tags=extra_tags
        )
        return redirect("register_student")

    # ✅ Otherwise (GET) → render list with filters
    handled_sections = HandledSection.objects.filter(teacher_id=teacher_id)
    if not handled_sections.exists():
        messages.error(request, "You are not assigned to any sections yet.", extra_tags=extra_tags)

    # 👇 sections for FILTER DROPDOWN only
    sections = []
    for hs in handled_sections:
        key = f"{hs.section.year_level.year}{hs.section.letter}"
        if not any(f"{s.year_level.year}{s.letter}" == key for s in sections):
            sections.append(hs.section)

    department = request.GET.get("department")
    section_filter = request.GET.get("filter_by")
    sort_by = request.GET.get("sort_by")
    sort_order = request.GET.get("sort_order")
    per_page = int(request.GET.get("per_page", 25))

    paginator = get_students_for_teacher(teacher_id, department, section_filter, sort_by, sort_order, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))

    if not page_obj.object_list:
        messages.error(request, "No students found for the selected filters.", extra_tags=extra_tags)

    teacher = Teacher.objects.get(id=teacher_id)
    departments = Department.objects.all()
    if not departments.exists():
        messages.error(request, "No departments available.", extra_tags=extra_tags)

    section_codes = SectionJoinCode.objects.filter(section__in=[hs.section for hs in handled_sections])
    # if not section_codes.exists():
    #     messages.error(request, "No join codes have been generated yet.", extra_tags=extra_tags)

    context = {
        "handled_sections": handled_sections,
        "username": f"{teacher.first_name} {teacher.last_name}",
        "role": Role.TEACHER,
        "page_obj": page_obj,
        "departments": departments,
        "sections": sections,  # 👈 filter dropdown only
        "department": department,
        "section": section_filter,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "per_page": per_page,
        "selected_department": department,
        "selected_section": section_filter,
        "section_codes": section_codes,
    }
    return render(request, "teacher/register_student.html", context)


# ----------------------------
# Edit Student
# ----------------------------
@session_login_required(role=Role.TEACHER)
def edit_student(request, student_id):
    teacher_id = request.session.get("user_id")

    if not teacher_id:
        return JsonResponse({"success": False, "message": "Unauthorized"}, status=401)

    teacher = get_object_or_404(Teacher, id=teacher_id)
    student = get_object_or_404(Student, id=student_id)

    handled_sections = (
        HandledSection.objects
        .filter(teacher=teacher)
        .select_related("section__year_level", "department")
        .order_by("department__name", "section__year_level__year", "section__letter")
    )

    # 🚨 Must handle student's current section
    if not handled_sections.filter(section=student.section).exists():
        return JsonResponse({"success": False, "message": "Not authorized"}, status=403)

    # -----------------------------
    # GET: Prefill modal
    # -----------------------------
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

    # -----------------------------
    # POST: Save updates
    # -----------------------------
    if request.method == "POST":
        first_name = request.POST.get("student_first_name_modal")
        last_name = request.POST.get("student_last_name_modal")
        section_id = request.POST.get("student_section_modal")

        if not first_name or not last_name or not section_id:
            messages.error(request, "All fields are required.", extra_tags="edit_message")
            return JsonResponse({"success": False})

        try:
            new_section = Section.objects.select_related("department", "year_level").get(id=section_id)
        except Section.DoesNotExist:
            messages.error(request, "Invalid section selected.", extra_tags="edit_message")
            return JsonResponse({"success": False})

        # 🚨 Ensure teacher really handles this section
        if not handled_sections.filter(section=new_section).exists():
            messages.error(request, "You are not authorized to assign this section.", extra_tags="edit_message")
            return JsonResponse({"success": False})

        # ✅ Apply updates
        student.first_name = first_name
        student.last_name = last_name
        student.section = new_section
        student.save()

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
    teacher_id = request.session.get("user_id")

    if not teacher_id:
        messages.error(request, "Unauthorized access. Please log in again.", extra_tags="edit_message")
        return JsonResponse({"success": False}, status=401)

    teacher = get_object_or_404(Teacher, id=teacher_id)
    student = get_object_or_404(Student, id=student_id)

    handled_sections = HandledSection.objects.filter(teacher=teacher).values_list("section_id", flat=True)
    if student.section_id not in handled_sections:
        messages.error(request, "You are not authorized to delete this student.", extra_tags="edit_message")
        return JsonResponse({"success": False}, status=403)

    if request.method in ["DELETE", "POST"]:
        student_name = f"{student.first_name} {student.last_name}"
        student.delete()
        messages.success(request, f"Student {student_name} deleted successfully.", extra_tags="edit_message")
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)
