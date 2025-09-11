from django.core.paginator import Paginator
from django.shortcuts import render, redirect

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import SimpleAdmin, Teacher
from StudentManagementSystem.models.log import Log
from StudentManagementSystem.models.roles import Role


def create_log(request, action, description, target_model=None, target_id=None):
    """Helper to create logs consistently."""

    user_id = request.session.get("user_id")
    role = request.session.get("role")
    ip = get_client_ip(request)

    actor_name = "Unknown"
    if role == Role.STUDENT:
        from StudentManagementSystem.models import Student
        user = Student.objects.filter(id=user_id).first()
        actor_name = f"{user.first_name} {user.last_name}" if user else "Unknown Student"
    elif role == Role.TEACHER:
        from StudentManagementSystem.models import Teacher
        user = Teacher.objects.filter(id=user_id).first()
        actor_name = f"{user.first_name} {user.last_name}" if user else "Unknown Teacher"
    elif role == Role.ADMIN:
        from StudentManagementSystem.models import SimpleAdmin
        user = SimpleAdmin.objects.filter(id=user_id).first()
        actor_name = f"{user.first_name} {user.last_name}" if user else "Unknown Admin"

    Log.objects.create(
        actor_id=user_id,
        role=role,
        action=action,
        description=description,
        target_model=target_model,
        target_id=target_id,
        ip_address=ip,
    )


def get_client_ip(request):
    """Extracts client IP from request headers."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip

@session_login_required(role=[Role.ADMIN, Role.TEACHER])
def view_log(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    admin = SimpleAdmin.objects.filter(id=user_id).first()
    teacher = Teacher.objects.filter(id=user_id).first()

    if not admin:
        return redirect('unified_logout')

    logs = Log.objects.all().order_by("-timestamp")

    # ✅ Pagination
    per_page = int(request.GET.get("per_page", 25))
    paginator = Paginator(logs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    username = None

    if role == Role.ADMIN:
        username = admin.username
    elif role == Role.TEACHER:
        username = f"{teacher.first_name} {teacher.last_name}"

    context = {
        "logs": page_obj.object_list,
        "page_obj": page_obj,
        "per_page": per_page,
        "sort_by": request.GET.get("sort_by", ""),
        "sort_order": request.GET.get("sort_order", ""),
        'role': role,
        'username': username,
    }

    return render(request, "logs.html", context)