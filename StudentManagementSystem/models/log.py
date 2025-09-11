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
    role = models.CharField(max_length=20, choices=Role.choices)

    # What action happened
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default="OTHER")
    description = models.TextField()  # human-readable description ("Edited student John Doe", etc.)

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
        formatted_time = self.timestamp.strftime("%B %d, %Y %I:%M %p")
        return f"[{formatted_time}] ({self.role}) → {self.action}"
