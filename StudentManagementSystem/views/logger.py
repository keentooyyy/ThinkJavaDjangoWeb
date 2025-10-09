from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.shortcuts import render, redirect

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import SimpleAdmin, Teacher, Student, Notification
from StudentManagementSystem.models.log import Log
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.teachers import HandledSection


def create_log(request=None, action=None, description=""):
    """Helper to create logs consistently, supports both authenticated and system actions."""

    # Default values
    user_id = None
    role = None
    ip = None

    # Try to extract session + IP if request provided
    if request:
        user_id = request.session.get("user_id")
        role = request.session.get("role")
        ip = get_client_ip(request)

    # ✅ Fallback for unauthenticated/system actions
    if not user_id or not role:
        user_id = "SYSTEM"
        role = "SYSTEM"

    Log.objects.create(
        actor_id=user_id,
        role=role,
        action=action or "UNKNOWN",
        description=description,
        ip_address=ip or "0.0.0.0",
    )


def get_client_ip(request):
    """Extracts client IP from request headers."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_filtered_logs_for_user(user_id, role):
    logs = Log.objects.all()

    if role == Role.ADMIN:
        # Admin sees all logs
        return logs

    if role == Role.TEACHER:
        teacher = Teacher.objects.filter(id=user_id).first()
        if not teacher:
            return Log.objects.none()

        # Sections this teacher handles
        handled_sections = HandledSection.objects.filter(
            teacher=teacher
        ).values_list("section_id", flat=True)

        # Students in those sections
        student_ids = Student.objects.filter(
            section_id__in=handled_sections
        ).values_list("id", flat=True)

        # Convert to string for Log.actor_id (CharField)
        student_ids = [str(sid) for sid in student_ids]

        return logs.filter(
            Q(actor_id=str(teacher.id), role=Role.TEACHER) |
            (Q(actor_id__in=student_ids) & Q(role=Role.STUDENT))
        )

    # Future: could add Role.STUDENT here if needed
    return Log.objects.none()


@session_login_required(role=[Role.ADMIN, Role.TEACHER])
def view_log(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    admin = SimpleAdmin.objects.filter(id=user_id).first()
    teacher = Teacher.objects.filter(id=user_id).first()

    if not (admin or teacher):
        return redirect("unified_logout")

    # Base queryset depending on role
    logs = get_filtered_logs_for_user(user_id, role)

    # ✅ Filters
    role_filter = request.GET.get("role", "")
    action_filter = request.GET.get("action", "")
    search_query = request.GET.get("search", "")

    if role_filter:
        logs = logs.filter(role=role_filter)

    if action_filter:
        logs = logs.filter(action=action_filter)

    if search_query:
        logs = logs.filter(
            Q(description__icontains=search_query) |
            Q(ip_address__icontains=search_query) |
            Q(actor_id__icontains=search_query)
        )

    # ✅ Order
    sort_order = request.GET.get("sort_order", "desc")
    logs = logs.order_by("timestamp" if sort_order == "asc" else "-timestamp")

    # ✅ Pagination
    per_page = int(request.GET.get("per_page", 25))
    paginator = Paginator(logs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ✅ Username for header
    username = None
    notifications = None
    unread_count = None
    if role == Role.ADMIN and admin:
        username = admin.username
    elif role == Role.TEACHER and teacher:
        username = f"{teacher.first_name} {teacher.last_name}"
        notifications = Notification.objects.filter(
            recipient_role=Role.TEACHER,
            teacher_recipient=teacher
        ).order_by("-created_at")  # last 10

        unread_count = notifications.filter(is_read=False).count()

    context = {
        "logs": page_obj.object_list,
        "page_obj": page_obj,
        "per_page": per_page,
        "sort_order": sort_order,
        "role_filter": role_filter,
        "action_filter": action_filter,
        "search_query": search_query,
        "role": role,
        "username": username,
        "role_choices": Role.choices,
        "action_choices": Log.ACTION_CHOICES,
        "notifications": notifications,
        "unread_count": unread_count,
    }

    return render(request, "logs.html", context)
