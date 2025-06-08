# StudentManagementSystem/models/section.py

from django.db import models

from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.year_level import YearLevel


class Section(models.Model):
    letter = models.CharField(max_length=1, unique=True)  # e.g. "A", "B", "C"


    def __str__(self):
        return f"{self.letter}"
