from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password

from StudentManagementSystem.models import SectionJoinCode, Student


def student_register(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        name = request.POST.get('name')
        password = request.POST.get('password')
        section_code = request.POST.get('section_code')

        # 🔍 Lookup section code
        try:
            join_code = SectionJoinCode.objects.get(code=section_code)
        except SectionJoinCode.DoesNotExist:
            messages.error(request, 'Invalid section code.')
            return redirect('student_register')

        if Student.objects.filter(student_id=student_id).exists():
            messages.error(request, 'Student ID already taken.')
            return redirect('student_register')

        Student.objects.create(
            student_id=student_id,
            name=name,
            password=make_password(password),
            department=join_code.department,
            year_level=join_code.year_level,
            section=join_code.section
        )

        messages.success(request, 'Registration successful. Please log in.')
        return redirect('student_login')

    return render(request, 'students/register.html')


def student_login(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        password = request.POST.get('password')

        try:
            student = Student.objects.get(student_id=student_id)
            if check_password(password, student.password):
                request.session['student_id'] = student.id
                messages.success(request, 'Login successful.')
                return redirect('student_dashboard')
            else:
                messages.error(request, 'Incorrect password.')
        except Student.DoesNotExist:
            messages.error(request, 'Student ID not found.')

    return render(request, 'students/login.html')


def student_logout(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully.')
    return redirect('student_login')
