from django.db import models

class AchievementDefinition(models.Model):
    code = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True)  # ✅ This is the only control you need

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


