from django.db import models

class AchievementDefinition(models.Model):
    code = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    unlocked = models.BooleanField(default=False)

    def __str__(self):
        return self.code
