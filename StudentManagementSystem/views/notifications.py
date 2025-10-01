from django.shortcuts import redirect
from django.http import HttpResponseForbidden

from StudentManagementSystem.views.notifications_helper import mark_notification_as_read, mark_all_notifications_as_read


def read_notification(request, notif_id):
    """Shared view to mark one notification as read (enforces ownership in utils)."""
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or not role:
        return HttpResponseForbidden("Invalid session.")

    success = mark_notification_as_read(notif_id, user_id, role)

    if not success:
        return HttpResponseForbidden("You are not allowed to read this notification.")

    # ✅ Redirect back to last page (or fallback to root)
    return redirect(request.META.get("HTTP_REFERER", "/"))


def mark_all_as_read_view(request):
    """Shared view to mark all notifications as read for the current user."""
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or not role:
        return HttpResponseForbidden("Invalid session.")

    mark_all_notifications_as_read(user_id, role)

    # ✅ Redirect back to last page (or fallback to root)
    return redirect(request.META.get("HTTP_REFERER", "/"))
