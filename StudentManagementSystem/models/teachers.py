# StudentManagementSystem/models/teacher.py
from django.db import models

from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.year_level import YearLevel


class Teacher(models.Model):
    teacher_id = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # store hashed passwords ideally
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TEACHER  # Default to 'Teacher' role
    )

    def __str__(self):
        return self.teacher_id


class HandledSection(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='handled_sections')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year_level = models.ForeignKey(YearLevel, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher', 'department', 'year_level', 'section')

    def __str__(self):
        return f"{self.teacher.teacher_id}: {self.department.name}{self.year_level.year}{self.section.letter}"

