from django.db import models

class LevelDefinition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unlocked = models.BooleanField(default=False)

    def __str__(self):
        return self.name
