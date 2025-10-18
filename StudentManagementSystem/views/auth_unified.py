import re

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect

from StudentManagementSystem.models import Student, Teacher, SimpleAdmin, SectionJoinCode
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.views.logger import create_log
from StudentManagementSystem.views.login_key import make_login_key
from StudentManagementSystem.views.notifications_helper import create_notification
from StudentManagementSystem.views.sync_all_progress import run_sync_in_background


def unified_login(request):
    if request.method == 'POST':
        user_id = request.POST.get('username')
        raw_password = request.POST.get('password')

        # 🔹 Check Student
        try:
            login_key = make_login_key(user_id, Role.STUDENT)
            student = Student.objects.get(login_key=login_key)
            if check_password(raw_password, student.password):
                request.session['user_id'] = student.id
                request.session['role'] = Role.STUDENT
                request.session['login_key'] = login_key
                create_log(request, "LOGIN", f"Student {student.first_name} {student.last_name} "
                                             f"(ID: {student.student_id}) has logged in.")
                return redirect('student_dashboard')
        except Student.DoesNotExist:
            pass

        # 🔹 Check Teacher
        try:
            login_key = make_login_key(user_id, Role.TEACHER)
            teacher = Teacher.objects.get(login_key=login_key)
            if check_password(raw_password, teacher.password):
                request.session['user_id'] = teacher.id
                request.session['role'] = Role.TEACHER
                request.session['login_key'] = login_key
                create_log(request, "LOGIN", f"Teacher {teacher.first_name} {teacher.last_name} "
                                             f"(ID: {teacher.teacher_id}) has logged in.")
                return redirect('teacher_dashboard')
        except Teacher.DoesNotExist:
            pass

        # 🔹 Check Admin
        try:
            admin = SimpleAdmin.objects.get(username=user_id)
            if check_password(raw_password, admin.password):
                request.session['user_id'] = admin.id
                request.session['role'] = Role.ADMIN
                request.session['login_key'] = f"ADMIN-{admin.id}"
                create_log(request, "LOGIN", f"Admin {admin.username} (System ID: {admin.id}) has logged in.")
                return redirect('admin_dashboard')
        except SimpleAdmin.DoesNotExist:
            pass

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


def register_student(request):
    if request.method == "POST":
        student_id = request.POST.get("username", "").strip()
        first_name = request.POST.get("firstname", "").strip()
        last_name = request.POST.get("lastname", "").strip()
        password = request.POST.get("password", "")
        re_password = request.POST.get("re_password", "")
        section_code = request.POST.get("section_code", "").strip()

        # --- Basic validation ---
        if not all([student_id, first_name, last_name, password, re_password, section_code]):
            messages.error(request, "Please fill out all required fields.")
            return redirect("register")

        if not re.match(r"^\d{2}-\d{4}-\d{3}$", student_id):
            messages.error(request, "Invalid student ID format. Use the format: YY-XXXX-XXX (e.g., 12-2345-678).")
            return redirect("register")

        # 🔒 Password length check
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect("register")

        if password != re_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        # --- Validate section code ---
        try:
            join_code = SectionJoinCode.objects.select_related("section", "year_level").get(code=section_code)
        except SectionJoinCode.DoesNotExist:
            messages.error(request, "Invalid section code. Please enter a valid one.")
            return redirect("register")

        # --- Check if student ID already exists ---
        if Student.objects.filter(student_id=student_id).exists():
            messages.error(request, "ID number already registered.")
            return redirect("register")

        # --- Create new Student record ---
        student = Student.objects.create(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password),
            year_level=join_code.year_level,
            section=join_code.section,
            role=Role.STUDENT,
        )
        run_sync_in_background()
        # --- Notify teacher(s) who handle this section ---
        handled_sections = HandledSection.objects.select_related("teacher").filter(
            section=join_code.section,
            department=join_code.department,
            year_level=join_code.year_level,
        )

        for handled in handled_sections:
            teacher = handled.teacher
            create_notification(
                request=request,
                recipient_role=Role.TEACHER,
                teacher_recipient=teacher,
                title="New Student Joined",
                message=(
                    f"{student.first_name} {student.last_name} "
                    f"has joined your section "
                    f"{handled.department.name}{handled.year_level.year}{handled.section.letter}."
                ),
                section_recipient=join_code.section,
            )

        # --- Log registration ---
        create_log(
            request,
            action="CREATE",
            description=(
                f"Student {student.first_name} {student.last_name} "
                f"registered successfully using section join code {section_code} "
                f"({join_code.department.name}{join_code.year_level.year}{join_code.section.letter})."
            ),
        )


        # --- Store session manually for @session_login_required ---
        request.session["user_id"] = student.id
        request.session["role"] = Role.STUDENT

        return redirect("student_dashboard")

    return render(request, "register.html")
