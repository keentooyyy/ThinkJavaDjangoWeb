from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect

from StudentManagementSystem.models import Student, Teacher, SimpleAdmin
from StudentManagementSystem.models.roles import Role


def unified_login(request):
    if request.method == 'POST':
        user_id = request.POST.get('username')
        raw_password = request.POST.get('password')

        # Check if the user is a Student
        try:
            student = Student.objects.get(student_id=user_id)
            if check_password(raw_password, student.password):
                request.session['user_id'] = student.id
                request.session['role'] = Role.STUDENT
                return redirect('student_dashboard')
        except Student.DoesNotExist:
            pass  # Continue to check for Teacher or Admin

        # Check if the user is a Teacher
        try:
            teacher = Teacher.objects.get(teacher_id=user_id)
            if check_password(raw_password, teacher.password):
                request.session['user_id'] = teacher.id
                request.session['role'] = Role.TEACHER
                return redirect('teacher_dashboard')
        except Teacher.DoesNotExist:
            pass  # Continue to check for Admin

        # Check if the user is an Admin
        try:
            admin = SimpleAdmin.objects.get(username=user_id)
            if check_password(raw_password, admin.password):
                request.session['user_id'] = admin.id
                request.session['role'] = Role.ADMIN
                return redirect('admin_dashboard')
        except SimpleAdmin.DoesNotExist:
            messages.error(request, 'Invalid credentials.')
            return redirect('unified_login')

    return render(request, 'login.html')


def unified_logout(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully.')
    return redirect('unified_login')

