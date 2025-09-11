from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect

from StudentManagementSystem.models import Student, Teacher, SimpleAdmin
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.views.logger import create_log


def unified_login(request):
    if request.method == 'POST':
        user_id = request.POST.get('username')
        raw_password = request.POST.get('password')

        # 🔹 Check Student
        try:
            student = Student.objects.get(student_id=user_id)
            if check_password(raw_password, student.password):
                request.session['user_id'] = student.id
                request.session['role'] = Role.STUDENT
                create_log(
                    request,
                    "LOGIN",
                    f"Student {student.first_name} {student.last_name} "
                    f"(ID: {student.student_id}) has logged in."
                )
                return redirect('student_dashboard')
            else:
                messages.error(request, 'Invalid credentials.')
                return redirect('unified_login')
        except Student.DoesNotExist:
            pass

        # 🔹 Check Teacher
        try:
            teacher = Teacher.objects.get(teacher_id=user_id)
            if check_password(raw_password, teacher.password):
                request.session['user_id'] = teacher.id
                request.session['role'] = Role.TEACHER
                create_log(
                    request,
                    "LOGIN",
                    f"Teacher {teacher.first_name} {teacher.last_name} "
                    f"(ID: {teacher.teacher_id}) has logged in."
                )
                return redirect('teacher_dashboard')
            else:
                messages.error(request, 'Invalid credentials.')
                return redirect('unified_login')
        except Teacher.DoesNotExist:
            pass

        # 🔹 Check Admin
        try:
            admin = SimpleAdmin.objects.get(username=user_id)
            if check_password(raw_password, admin.password):
                request.session['user_id'] = admin.id
                request.session['role'] = Role.ADMIN
                create_log(
                    request,
                    "LOGIN",
                    f"Admin {admin.username} (System ID: {admin.id}) has logged in."
                )
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid credentials.')
                return redirect('unified_login')
        except SimpleAdmin.DoesNotExist:
            messages.error(request, 'Invalid credentials.')
            return redirect('unified_login')

    return render(request, 'login.html')



def unified_logout(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if role == Role.STUDENT:
        student = Student.objects.filter(id=user_id).first()
        if student:
            create_log(
                request,
                "LOGOUT",
                f"Student {student.first_name} {student.last_name} "
                f"(ID: {student.student_id}) has logged out."
            )

    elif role == Role.TEACHER:
        teacher = Teacher.objects.filter(id=user_id).first()
        if teacher:
            create_log(
                request,
                "LOGOUT",
                f"Teacher {teacher.first_name} {teacher.last_name} "
                f"(ID: {teacher.teacher_id}) has logged out."
            )

    elif role == Role.ADMIN:
        admin = SimpleAdmin.objects.filter(id=user_id).first()
        if admin:
            create_log(
                request,
                "LOGOUT",
                f"Admin {admin.username} (System ID: {admin.id}) has logged out."
            )

    # ✅ flush AFTER logging
    request.session.flush()
    messages.success(request, 'Logged out successfully.')
    return redirect('unified_login')

