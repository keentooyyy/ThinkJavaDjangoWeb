from django.db import models

from StudentManagementSystem.models.student import Student
from .achievement_definition import AchievementDefinition


class AchievementProgress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    achievement = models.ForeignKey(AchievementDefinition, on_delete=models.CASCADE)
    unlocked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'achievement')
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["unlocked"]),
        ]
