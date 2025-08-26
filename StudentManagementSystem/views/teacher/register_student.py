# StudentManagementSystem/views/teacher/register_student.py

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect, render

from StudentManagementSystem.models import Student
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.teachers import HandledSection, Teacher


def register_student(request):
    teacher_id = request.session.get('user_id')
    if not teacher_id:
        messages.error(request, "Unauthorized access.")
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

        if not (student_id and password and section_id):
            messages.error(request, "All fields are required.")
            return redirect('register_student')



        selected_handled = handled_sections.filter(section_id=section_id).first()
        # print(selected_handled.section_id)
        if not selected_handled:
            messages.error(request, "You are not allowed to assign this section.")
            return redirect('register_student')

        if Student.objects.filter(student_id=student_id).exists():
            messages.error(request, "Student ID already exists.")
            return redirect('register_student')

        student = Student(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            section_id=selected_handled.section_id,
            role=Role.STUDENT
        )
        student.save()

    teacher = Teacher.objects.get(id=teacher_id)
    full_name = teacher.first_name + " " + teacher.last_name
    role = Role.TEACHER
    context = {
        'handled_sections': handled_sections,
        'username': full_name,
        'role': role,
    }



    return render(request, 'teacher/register_student.html', context)
