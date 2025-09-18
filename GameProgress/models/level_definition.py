from django.db import models

class LevelDefinition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unlocked = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=999)

    class Meta:
        ordering = ["sort_order"]

    def save(self, *args, **kwargs):
        # Auto-assign sort_order if not explicitly set
        if self.sort_order == 999:
            if self.name == "Tutorial":
                self.sort_order = 0
            elif self.name.startswith("Level"):
                try:
                    num = int(self.name.replace("Level", ""))
                    self.sort_order = num
                except ValueError:
                    self.sort_order = 999
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
