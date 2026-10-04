import uuid
from django.db import models
class Job(models.Model):
    class Status(models.TextChoices):
        QUEUED="queued","Queued"
        RUNNING="running","Running"
        SUCCEEDED="succeeded","Succeeded"
        FAILED="failed","Failed"
    id=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key=models.CharField(max_length=128, unique=True)
    operation=models.CharField(max_length=64)
    payload=models.JSONField(default=dict)
    result=models.JSONField(null=True, blank=True)
    status=models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    attempts=models.PositiveIntegerField(default=0)
    error=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
