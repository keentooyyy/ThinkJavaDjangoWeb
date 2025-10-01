# StudentManagementSystem/models/notification.py

from django.db import models
from django.utils.timezone import now

from StudentManagementSystem.models import Teacher
from StudentManagementSystem.models.roles import Role

from StudentManagementSystem.models.student import Student
from StudentManagementSystem.models.section import Section



class Notification(models.Model):
    # Who sent it
    sender_role = models.CharField(max_length=20, choices=Role.choices)
    sender_id = models.CharField(max_length=50)  # store admin_id, teacher_id, etc. as string

    # Who receives it
    recipient_role = models.CharField(max_length=20, choices=Role.choices)
    teacher_recipient = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications"
    )
    student_recipient = models.ForeignKey(
        Student, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications"
    )
    section_recipient = models.ForeignKey(
        Section, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications"
    )

    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(default=now)
    is_read = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["recipient_role", "is_read"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.recipient_role}] {self.title} - {self.message[:30]}..."
