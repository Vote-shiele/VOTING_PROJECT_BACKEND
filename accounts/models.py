from django.db import models

class Admin(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Store hashed password

    def __str__(self):
        return self.username


class AdminLog(models.Model):
    ACTION_CHOICES = [
        ('EDIT_CANDIDATE', 'Edit Candidate'),
        ('DELETE_POLL', 'Delete Poll'),
        ('EDIT_POLL', 'Edit Poll'),
    ]

    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f"{self.admin.username} {self.get_action_display()} at {self.timestamp}"

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

    def get_total_votes(self):
        return VoteLog.objects.filter(poll=self).count()

    def get_candidate_votes(self):
        candidates = self.candidate_set.all()
        return {candidate.id: candidate.votelog_set.count() for candidate in candidates}

class Candidate(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='candidates/', blank=True, null=True)
    description = models.TextField(blank=True)

    def get_edit_history(self):
        return AdminLog.objects.filter(
            action='EDIT_CANDIDATE',
            details__contains=f"candidate_id={self.id}"
        ).order_by('-timestamp')

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



class VoteLog(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, null=True, blank=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        voter_name = self.voter.username if self.voter else "Anonymous"
        return f"{voter_name} voted for {self.candidate.name} at {self.voted_at}"