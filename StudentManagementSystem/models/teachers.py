# StudentManagementSystem/models/teacher.py
from datetime import date

from django.db import models

from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.year_level import YearLevel


class Teacher(models.Model):
    teacher_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)  # store hashed passwords ideally
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TEACHER
    )

    class Meta:
        indexes = [
            models.Index(fields=['teacher_id']),
            models.Index(fields=['last_name', 'first_name']),
        ]

    def __str__(self):
        return self.teacher_id


class HandledSection(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='handled_sections')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year_level = models.ForeignKey(YearLevel, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher', 'department', 'year_level', 'section')
        indexes = [
            models.Index(fields=['teacher', 'department', 'year_level', 'section']),  # Composite index for teacher + section
        ]

    def __str__(self):
        return f"{self.teacher.teacher_id}: {self.department.name}{self.year_level.year}{self.section.letter}"
