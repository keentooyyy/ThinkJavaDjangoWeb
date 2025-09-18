from django.db import models

from StudentManagementSystem.models.pre_post_test import StudentTest, TestDefinition
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.year_level import YearLevel
from StudentManagementSystem.views.login_key import make_login_key

# 🔹 import test + level models
from GameProgress.models.level_progress import LevelProgress
from GameProgress.models.level_definition import LevelDefinition


class Student(models.Model):
    student_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    year_level = models.ForeignKey(YearLevel, on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )
    login_key = models.CharField(max_length=128, unique=True, editable=False, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['year_level', 'section']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"

    def save(self, *args, **kwargs):
        # generate login_key
        self.login_key = make_login_key(self.student_id, self.role)
        super().save(*args, **kwargs)

    @property
    def full_section(self):
        if self.section:
            return f"{self.section.department.name}{self.section.year_level.year}{self.section.letter}"
        return "N/A"

    # --------------------------
    # 🔹 Test & Progress Helpers
    # --------------------------

    @property
    def has_taken_pretest(self):
        """True if student has a completed Pre-Test"""
        return StudentTest.objects.filter(
            student=self,
            test__test_type=TestDefinition.PRE,
            completed=True
        ).exists()

    @property
    def has_taken_posttest(self):
        """True if student has a completed Post-Test"""
        return StudentTest.objects.filter(
            student=self,
            test__test_type=TestDefinition.POST,
            completed=True
        ).exists()

    @property
    def all_levels_completed(self):
        """True if student has completed all levels in the game"""
        total_levels = LevelDefinition.objects.count()
        completed_levels = LevelProgress.objects.filter(student=self, unlocked=True).count()
        return total_levels > 0 and completed_levels == total_levels

    @property
    def can_take_posttest(self):
        """Only allowed if:
        1. Pre-test taken
        2. All levels completed
        3. Post-test not yet taken
        """
        return self.has_taken_pretest and self.all_levels_completed and not self.has_taken_posttest

    @property
    def test_status(self):
        """Return a dictionary for API response"""
        return {
            "student_id": self.student_id,
            "has_taken_pretest": self.has_taken_pretest,
            "has_taken_posttest": self.has_taken_posttest,
            "all_levels_completed": self.all_levels_completed,
            "can_take_posttest": self.can_take_posttest,
        }
