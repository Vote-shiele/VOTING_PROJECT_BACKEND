from django.db import models

class Admin(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Store hashed password

    def __str__(self):
        return self.username

from django.utils import timezone

class Poll(models.Model):
    POLL_TYPES = (
        ('public', 'Public'),
        ('private', 'Private'),
    )

    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    poll_type = models.CharField(max_length=10, choices=POLL_TYPES)
    description = models.TextField(blank=True, null=True) #Update the Poll model for search bar
    def __str__(self):
        return self.name

class Candidate(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='candidates/', blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.poll.name})"

class Voter(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    username = models.CharField(max_length=150)
    email = models.EmailField()
    password = models.CharField(max_length=255)  # Will store hashed password
    has_voted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.poll.name})"