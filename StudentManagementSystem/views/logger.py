from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.shortcuts import render, redirect

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import SimpleAdmin, Teacher, Student
from StudentManagementSystem.models.log import Log
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.teachers import HandledSection


def create_log(request, action, description):
    """Helper to create logs consistently."""

    user_id = request.session.get("user_id")
    role = request.session.get("role")
    ip = get_client_ip(request)

    Log.objects.create(
        actor_id=user_id,
        role=role,
        action=action,
        description=description,
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

    # ✅ Filter logs based on role
    logs = get_filtered_logs_for_user(user_id, role)

    # ✅ Sorting
    sort_by = request.GET.get("sort_by", "")
    sort_order = request.GET.get("sort_order", "")
    if sort_by:
        order = f"-{sort_by}" if sort_order == "desc" else sort_by
        logs = logs.order_by(order)
    else:
        logs = logs.order_by("-timestamp")

    # ✅ Pagination
    per_page = int(request.GET.get("per_page", 25))
    paginator = Paginator(logs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ✅ Username
    username = None
    if role == Role.ADMIN and admin:
        username = admin.username
    elif role == Role.TEACHER and teacher:
        username = f"{teacher.first_name} {teacher.last_name}"

    context = {
        "logs": page_obj.object_list,
        "page_obj": page_obj,
        "per_page": per_page,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "role": role,
        "username": username,
    }

    return render(request, "logs.html", context)