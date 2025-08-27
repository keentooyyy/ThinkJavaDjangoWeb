# StudentManagementSystem/views/teacher/register_student.py

from django.contrib import messages
from django.core.paginator import Paginator
from django.http.response import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404

from StudentManagementSystem.decorators.custom_decorators import session_login_required

from StudentManagementSystem.models import Student, SectionJoinCode
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.teachers import HandledSection, Teacher


def get_students_for_teacher(teacher_id, department=None, section=None, sort_by=None, sort_order=None, per_page=25):
    # Fetch all sections handled by the teacher
    handled_sections = HandledSection.objects.filter(teacher_id=teacher_id)

    # Get students in these sections
    students = Student.objects.filter(section__in=[section.section for section in handled_sections])

    # Apply department filter if provided
    if department:
        students = students.filter(section__department__name=department)

    # Apply section filter if provided
    if section:
        # Assume section is in the format "1A" (year+letter)
        year = section[:1]  # First part for year (e.g., '1' from '1A')
        letter = section[1:]  # Second part for letter (e.g., 'A' from '1A')

        # Apply filter for section based on year_level and letter
        students = students.filter(section__year_level__year=year, section__letter=letter)

    # Apply sorting if requested
    if sort_by:
        if sort_order == 'desc':
            students = students.order_by(f"-{sort_by}")
        else:
            students = students.order_by(f"{sort_by}")
    else:
        # Default order if no sort_by is provided
        students = students.order_by('student_id')  # Adjust to default field of your choice

    # Paginate the students
    paginator = Paginator(students, per_page)  # Show 'per_page' students per page
    return paginator


@session_login_required(role=Role.TEACHER)
def register_student(request):
    extra_tags = 'create_message'  # This can be added to the message for additional styling or handling
    teacher_id = request.session.get('user_id')

    if not teacher_id:
        messages.error(request, "Unauthorized access. You need to log in first.", extra_tags=extra_tags)
        return redirect('unified_logout')

    # Fetch sections handled by the teacher
    handled_sections = HandledSection.objects.filter(teacher_id=teacher_id)

    # Initialize an empty list to store unique sections
    sections = []
    for handled_section in handled_sections:
        section = handled_section.section
        section_key = f"{section.year_level.year}{section.letter}"  # Concatenate year and letter

        # Check if section (year + letter) is already in the list (ignoring department)
        if not any(f"{s.year_level.year}{s.letter}" == section_key for s in sections):
            sections.append(section)

    # Get filter values from the GET request
    department = request.GET.get('department', None)
    section_filter = request.GET.get('filter_by', None)
    sort_by = request.GET.get('sort_by', None)
    sort_order = request.GET.get('sort_order', None)
    per_page = int(request.GET.get('per_page', 25))  # Default to 25 items per page

    # Get the filtered and paginated students
    paginator = get_students_for_teacher(teacher_id, department, section_filter, sort_by, sort_order, per_page)

    # Get the current page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Fetch teacher details for the logged-in user
    teacher = Teacher.objects.get(id=teacher_id)
    full_name = teacher.first_name + " " + teacher.last_name
    role = Role.TEACHER

    # Fetch departments for the filter dropdowns
    departments = Department.objects.all()  # Adjust based on your models
    section_codes = SectionJoinCode.objects.filter(section__in=[hs.section for hs in handled_sections])
    print(f"section_codes {section_codes}")


    # Context for rendering the page
    context = {'handled_sections': handled_sections, 'username': full_name, 'role': role, 'page_obj': page_obj,
        'departments': departments, 'sections': sections,  # Only show unique sections handled by the teacher
        'department': department, 'section': section_filter, 'sort_by': sort_by, 'sort_order': sort_order,
        'per_page': per_page, 'selected_department': department, 'selected_section': section_filter, 'section_codes': section_codes,}

    return render(request, 'teacher/register_student.html', context)


@session_login_required(role=Role.TEACHER)
def edit_student(request, student_id):
    teacher_id = request.session.get("user_id")

    if not teacher_id:
        messages.error(request, "Unauthorized access. Please log in again.", extra_tags="edit_message")
        return JsonResponse({"success": False})

    teacher = get_object_or_404(Teacher, id=teacher_id)
    student = get_object_or_404(Student, id=student_id)

    # Make sure the student belongs to this teacher
    handled_sections = HandledSection.objects.filter(teacher=teacher).values_list("section_id", flat=True)
    if student.section_id not in handled_sections:
        messages.error(request, "You are not authorized to edit this student.", extra_tags="edit_message")
        return JsonResponse({"success": False})

    # ✅ GET request → return student details
    if request.method == "GET":
        return JsonResponse({
            "success": True,
            "student": {
                "id": student.id,
                "student_id": student.student_id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "full_section": f"{student.section.year_level.year}{student.section.letter}",
            }
        })

    # ✅ POST request → update student
    if request.method == "POST":
        first_name = request.POST.get("student_first_name_modal")
        last_name = request.POST.get("student_last_name_modal")
        section_key = request.POST.get("student_section_modal")

        if not first_name or not last_name or not section_key:
            messages.error(request, "All fields are required.", extra_tags="edit_message")
            return JsonResponse({"success": False})

        year, letter = section_key[0], section_key[1:]

        try:
            new_section = student.section.__class__.objects.get(
                year_level__year=year,
                letter=letter,
                department=student.section.department,
            )
        except Exception:
            messages.error(request, "Invalid section selected.", extra_tags="edit_message")
            return JsonResponse({"success": False})

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

    # ✅ Fallback if method not allowed
    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)



@session_login_required(role=Role.TEACHER)
def delete_student(request, student_id):
    teacher_id = request.session.get("user_id")

    if not teacher_id:
        messages.error(request, "Unauthorized access. Please log in again.", extra_tags="edit_message")
        return JsonResponse({"success": False}, status=401)

    teacher = get_object_or_404(Teacher, id=teacher_id)
    student = get_object_or_404(Student, id=student_id)

    # Check authorization
    handled_sections = HandledSection.objects.filter(teacher=teacher).values_list("section_id", flat=True)
    if student.section_id not in handled_sections:
        messages.error(request, "You are not authorized to delete this student.", extra_tags="edit_message")
        return JsonResponse({"success": False}, status=403)

    if request.method == "DELETE" or request.method == "POST":
        student_name = f"{student.first_name} {student.last_name}"
        student.delete()
        messages.success(request, f"Student {student_name} deleted successfully.", extra_tags="edit_message")
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)