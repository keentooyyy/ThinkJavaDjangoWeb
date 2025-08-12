# StudentManagementSystem/views/teacher/register_student_teacher.py

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect

from StudentManagementSystem.models import Student
from StudentManagementSystem.models.teachers import HandledSection


def register_student_teacher(request):
    teacher_id = request.session.get('teacher_id')
    if not teacher_id or request.method != 'POST':
        messages.error(request, "Unauthorized access.")
        return redirect('teacher_dashboard')

    student_id = request.POST.get('student_id')
    password = request.POST.get('password')
    section_id = request.POST.get('section_id')

    if not (student_id and password and section_id):
        messages.error(request, "All fields are required.")
        return redirect('teacher_dashboard')

    # Use filter + first to avoid MultipleObjectsReturned
    handled_sections = HandledSection.objects.filter(
        teacher_id=teacher_id
    ).select_related('section', 'department', 'year_level')

    selected_handled = handled_sections.filter(section_id=section_id).first()
    if not selected_handled:
        messages.error(request, "You are not allowed to assign this section.")
        return redirect('teacher_dashboard')

    if Student.objects.filter(student_id=student_id).exists():
        messages.error(request, "Student ID already exists.")
        return redirect('teacher_dashboard')

    student = Student(
        student_id=student_id,
        name="",
        department=selected_handled.department,
        year_level=selected_handled.year_level,
        section=selected_handled.section,
        password=make_password(password)
    )
    student.save()

    messages.success(request, f"Student '{student_id}' registered successfully.")
    return redirect('teacher_dashboard')

