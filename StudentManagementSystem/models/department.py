

from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g. "CS", "IT"

    def __str__(self):
        return self.name
