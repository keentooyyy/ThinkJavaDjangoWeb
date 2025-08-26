# StudentManagementSystem/views/teacher/register_student.py

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect, render

from StudentManagementSystem.models import Student
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.teachers import HandledSection, Teacher


def register_student(request):
    extra_tags = 'create_message'  # This can be added to the message for additional styling or handling
    teacher_id = request.session.get('user_id')
    if not teacher_id:
        messages.error(request, "Unauthorized access. You need to log in first.", extra_tags=extra_tags)
        return redirect('unified_logout')

    # Use filter + first to avoid MultipleObjectsReturned
    handled_sections = HandledSection.objects.filter(
        teacher_id=teacher_id
    ).select_related('section', 'department', 'year_level')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        # Default password 123
        password = "123"
        section_id = request.POST.get('section_id')

        # Check if any required fields are missing
        if not (student_id and first_name and last_name and password and section_id):
            messages.error(request, "Please fill in all required fields: Student ID, First Name, Last Name, and Section.", extra_tags=extra_tags)
            return redirect('register_student')

        selected_handled = handled_sections.filter(section_id=section_id).first()
        if not selected_handled:
            messages.error(request, "You are not authorized to assign this section. Please select a valid section.", extra_tags=extra_tags)
            return redirect('register_student')

        if Student.objects.filter(student_id=student_id).exists():
            messages.error(request, f"Student ID already exists. Please use a unique student ID.", extra_tags=extra_tags)
            return redirect('register_student')

        # Create and save the new student
        student = Student(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            section_id=selected_handled.section_id,
            role=Role.STUDENT
        )
        student.save()

        # If successful, you can also show a success message (optional)
        messages.success(request, f"Student has been successfully registered!", extra_tags=extra_tags)

    # Fetch teacher details for the logged-in user
    teacher = Teacher.objects.get(id=teacher_id)
    full_name = teacher.first_name + " " + teacher.last_name
    role = Role.TEACHER

    context = {
        'handled_sections': handled_sections,
        'username': full_name,
        'role': role,
    }

    return render(request, 'teacher/register_student.html', context)

