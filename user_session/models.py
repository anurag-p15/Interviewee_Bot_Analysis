from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    username = models.EmailField(unique=True)  # Assuming username is email for simplicity
    password = models.CharField(max_length=128)  # Storing hashed passwords
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.username


from django.db import models

class InterviewResult(models.Model):
    username = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    num_questions = models.IntegerField()
    completion_time = models.DateTimeField(auto_now_add=True)
    analysis_results = models.JSONField()
    emotion_data = models.JSONField()
    bar_chart_data = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.username} - {self.domain}"


