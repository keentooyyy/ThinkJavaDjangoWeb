from django.db import models

from StudentManagementSystem.models.student import Student
from .level_definition import LevelDefinition


class LevelProgress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    level = models.ForeignKey(LevelDefinition, on_delete=models.CASCADE)
    best_time = models.PositiveIntegerField(default=0)
    current_time = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('student', 'level')
