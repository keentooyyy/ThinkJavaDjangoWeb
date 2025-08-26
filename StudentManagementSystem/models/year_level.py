# StudentManagementSystem/models/year_level.py

from django.db import models

class YearLevel(models.Model):
    year = models.PositiveSmallIntegerField(unique=True)  # e.g. 1, 2, 3, 4

    class Meta:
        indexes = [
            models.Index(fields=['year']),  # Index for year_level year field
        ]

    def __str__(self):
        return f"{self.year}"
