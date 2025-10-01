from StudentManagementSystem.models import Notification, Teacher, Student
from StudentManagementSystem.models.roles import Role


def create_notification(
    request,
    recipient_role,
    title,
    message,
    teacher_recipient=None,
    student_recipient=None,
    section_recipient=None
):
    """
    Helper to create notifications consistently.
    """

    sender_id = request.session.get("user_id")
    sender_role = request.session.get("role")

    if not sender_id or not sender_role:
        raise ValueError("Sender must be logged in to create a notification.")

    Notification.objects.create(
        sender_role=sender_role,
        sender_id=str(sender_id),
        recipient_role=recipient_role,
        teacher_recipient=teacher_recipient,
        student_recipient=student_recipient,
        section_recipient=section_recipient,
        title=title,
        message=message,
    )
    return True


def mark_notification_as_read(notification_id, user_id, role):
    """
    Mark a single notification as read — only if it belongs to the current user.
    Returns True if updated, False otherwise.
    """
    qs = Notification.objects.filter(id=notification_id, recipient_role=role)

    if role == Role.TEACHER:
        qs = qs.filter(teacher_recipient_id=user_id)
    elif role == Role.STUDENT:
        qs = qs.filter(student_recipient_id=user_id)
    elif role == Role.ADMIN:
        # Admins: recipient_role must be ADMIN (already filtered above)
        pass
    else:
        return False  # unsupported role

    return qs.update(is_read=True) > 0


def mark_all_notifications_as_read(user_id, role):
    """
    Mark all notifications for a user as read — only their own.
    """
    qs = Notification.objects.filter(recipient_role=role)

    if role == Role.TEACHER:
        qs = qs.filter(teacher_recipient_id=user_id)
    elif role == Role.STUDENT:
        qs = qs.filter(student_recipient_id=user_id)
    elif role == Role.ADMIN:
        # All admin notifications
        pass
    else:
        return 0

    return qs.update(is_read=True)
