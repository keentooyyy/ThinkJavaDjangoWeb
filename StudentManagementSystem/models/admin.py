from django.db import models

class SimpleAdmin(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  # You can hash passwords if needed

    def __str__(self):
        return self.username
