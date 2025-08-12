from datetime import date

from django.db import models

from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.year_level import YearLevel


class Student(models.Model):
    student_id = models.CharField(max_length=50, unique=True)  # unique username or ID
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    password = models.CharField(max_length=128)  # should be hashed
    year_level = models.ForeignKey(YearLevel, on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT  # Default to 'Student' role
    )

    def __str__(self):
        return f"{self.name} ({self.student_id})"

    @property
    def full_section(self):
        if self.section:
            return f"{self.section.department.name}{self.section.year_level.year}{self.section.letter}"
        return "N/A"

    def age(self):
        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or (
                today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        return age
