# StudentManagementSystem/utils/notifications.py
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


def mark_notification_as_read(notification_id):
    """Mark a single notification as read."""
    Notification.objects.filter(id=notification_id).update(is_read=True)


def mark_all_notifications_as_read(user_id, role):
    """Mark all notifications for a user as read."""
    qs = Notification.objects.filter(recipient_role=role)

    if role == Role.TEACHER:
        teacher = Teacher.objects.filter(id=user_id).first()
        if teacher:
            qs = qs.filter(teacher_recipient=teacher)

    elif role == Role.STUDENT:
        student = Student.objects.filter(id=user_id).first()
        if student:
            qs = qs.filter(student_recipient=student)

    qs.update(is_read=True)
