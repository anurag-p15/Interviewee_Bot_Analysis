from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    username = models.EmailField(unique=True)  # Assuming username is email for simplicity
    password = models.CharField(max_length=128)  # Storing hashed passwords
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.username
