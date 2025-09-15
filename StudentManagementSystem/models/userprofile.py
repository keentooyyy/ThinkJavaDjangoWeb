from datetime import date

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class UserProfile(models.Model):
    # Generic link: Teacher, Student, or SimpleAdmin
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    user_object = GenericForeignKey('content_type', 'object_id')

    # Personal details
    picture = models.ImageField(upload_to="", null=True, blank=True)
    middle_initial = models.CharField(max_length=5, null=True, blank=True)
    suffix = models.CharField(max_length=20, null=True, blank=True)  # Jr., Sr., III
    date_of_birth = models.DateField(null=True, blank=True)

    # Parents / Guardians
    father_name = models.CharField(max_length=150, null=True, blank=True)
    mother_name = models.CharField(max_length=150, null=True, blank=True)

    # Extra details
    bio = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    street = models.TextField(null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    barangay = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"Profile of {self.user_object}"

    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or (
            today.month == self.date_of_birth.month and today.day < self.date_of_birth.day
        ):
            age -= 1
        return age


class EducationalBackground(models.Model):
    profile = models.ForeignKey(
        "UserProfile",
        on_delete=models.CASCADE,
        related_name="educational_backgrounds"
    )
    institution = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    graduation_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.institution} ({self.start_date} - {self.graduation_date})"