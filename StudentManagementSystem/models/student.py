from datetime import date

from django.db import models

from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.year_level import YearLevel


class Student(models.Model):
    student_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    year_level = models.ForeignKey(YearLevel, on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )

    class Meta:
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['year_level', 'section']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"

    @property
    def full_section(self):
        if self.section:
            return f"{self.section.department.name}{self.section.year_level.year}{self.section.letter}"
        return "N/A"