from django.db import models
from django.contrib.auth.hashers import make_password

from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.year_level import YearLevel

class Student(models.Model):
    student_id = models.CharField(max_length=50, unique=True)  # unique username or ID
    name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)  # should be hashed
    year_level = models.ForeignKey(YearLevel, on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"

    @property
    def full_section(self):
        if self.section:
            return f"{self.section.department.name}{self.section.year_level.year}{self.section.letter}"
        return "N/A"
