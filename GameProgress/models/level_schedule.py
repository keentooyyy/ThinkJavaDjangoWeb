from django.db import models

from GameProgress.models import LevelDefinition
from StudentManagementSystem.models.section import Section


class SectionLevelSchedule(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    level = models.ForeignKey(LevelDefinition, on_delete=models.CASCADE)
    start_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("section", "level")

    def __str__(self):
        return f"{self.section} - {self.level.name} ({self.start_date} → {self.due_date})"
