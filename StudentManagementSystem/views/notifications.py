from django.http.response import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden

from StudentManagementSystem.models import Notification
from StudentManagementSystem.models.roles import Role
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


def delete_notification(request, notif_id):
    """Delete a notification belonging to the logged-in user."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or not role:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    notif = get_object_or_404(Notification, id=notif_id)

    # Ensure only the rightful owner can delete
    if role == Role.TEACHER and notif.teacher_recipient_id != user_id:
        return JsonResponse({"error": "Forbidden"}, status=403)
    if role == Role.STUDENT and notif.student_recipient_id != user_id:
        return JsonResponse({"error": "Forbidden"}, status=403)
    if role == Role.ADMIN and notif.recipient_role != Role.ADMIN:
        return JsonResponse({"error": "Forbidden"}, status=403)

    notif.delete()
    return JsonResponse({"success": True})