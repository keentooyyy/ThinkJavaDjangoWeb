# StudentManagementSystem/models/section.py

from django.db import models

from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.year_level import YearLevel


class Section(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)  # Link to Department model
    year_level = models.ForeignKey(YearLevel, on_delete=models.CASCADE)  # Link to YearLevel model
    letter = models.CharField(max_length=1)  # e.g., "A", "B", "C"

    class Meta:
        unique_together = ('department', 'year_level', 'letter')  # Ensure unique combination of department, year, and section letter
        indexes = [
            models.Index(fields=['department', 'year_level', 'letter']),  # Index for composite of department, year_level, and letter
        ]

    def __str__(self):
        return f"{self.department.name}{self.year_level.year}{self.letter}"  # e.g., "CS 1A"


