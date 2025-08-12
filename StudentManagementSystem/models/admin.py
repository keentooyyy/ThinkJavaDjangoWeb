from django.db import models

from StudentManagementSystem.models.roles import Role


class SimpleAdmin(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  # You can hash passwords if needed
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN  # Default to 'Admin' role
    )

    def __str__(self):
        return self.username
