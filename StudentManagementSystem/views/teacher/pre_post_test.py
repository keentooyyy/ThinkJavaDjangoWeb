from django.shortcuts import render

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.views.teacher.dashboard_teacher import get_teacher_dashboard_context


@session_login_required(role=Role.TEACHER)
def pre_post_test_view(request):
    teacher = request.user_obj
    username = f"{teacher.first_name} {teacher.last_name}"
    role = teacher.role
    context = {
        'username': username,
        'role': role,
    }
    return render(request, 'teacher/main/pre_post_test.html' ,context)