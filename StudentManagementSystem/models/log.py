from django.db import models
from django.utils.timezone import now

from StudentManagementSystem.models.roles import Role


class Log(models.Model):
    ACTION_CHOICES = [
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("VIEW", "View"),
        ("OTHER", "Other"),
    ]

    # Who did the action
    actor_id = models.CharField(max_length=50)  # can store student_id, teacher_id, or admin_id
    actor_name = models.CharField(max_length=150)  # for readability
    role = models.CharField(max_length=20, choices=Role.choices)

    # What action happened
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default="OTHER")
    description = models.TextField()  # human-readable description ("Edited student John Doe", etc.)

    # Extra context
    target_model = models.CharField(max_length=50, blank=True, null=True)  # e.g. "Student", "Teacher"
    target_id = models.CharField(max_length=50, blank=True, null=True)  # e.g. student_id, teacher_id

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(default=now)

    class Meta:
        indexes = [
            models.Index(fields=["actor_id", "role"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["action"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.actor_name} ({self.role}) → {self.action}"
