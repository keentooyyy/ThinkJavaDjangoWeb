# StudentManagementSystem/models/section.py

from django.db import models

class Section(models.Model):
    letter = models.CharField(max_length=1, unique=True)  # e.g. "A", "B", "C"

    def __str__(self):
        return self.letter
