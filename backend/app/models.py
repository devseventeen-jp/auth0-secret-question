from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator

class Auth0UsernameValidator(UnicodeUsernameValidator):
    regex = r'^[\w.@+-|]+$'

class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_/| only.',
        validators=[Auth0UsernameValidator()],
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    auth0_sub = models.CharField(max_length=255, unique=True, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    has_answered = models.BooleanField(default=False)
    secret_answer = models.TextField(null=True, blank=True)
    real_name = models.CharField(max_length=255, null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.username

class ApprovalLog(models.Model):
    ACTION_CHOICES = [
        ('SUBMITTED', 'Submitted Answer'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_logs')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_performed')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"
