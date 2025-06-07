# StudentManagementSystem/models/year_level.py

from django.db import models

class YearLevel(models.Model):
    year = models.PositiveSmallIntegerField(unique=True)  # e.g. 1, 2, 3, 4

    def __str__(self):
        return f"{self.year}"
