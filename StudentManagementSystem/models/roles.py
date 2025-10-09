from django.db import models


class Role(models.TextChoices):
    STUDENT = 'STUDENT', 'Student'
    TEACHER = 'TEACHER', 'Teacher'
    ADMIN = 'ADMIN', 'Admin'
