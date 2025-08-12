# StudentManagementSystem/models/section_code.py

from django.db import models

from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.year_level import YearLevel


class SectionJoinCode(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year_level = models.ForeignKey(YearLevel, on_delete=models.CASCADE)
    code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('section', 'department', 'year_level')

    def __str__(self):
        return f"{self.department.name}{self.year_level.year}{self.section.letter} → {self.code}"
