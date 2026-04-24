from django.db import models
from django.contrib.auth.models import User

class AutoFlowWorkflow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default="DRAFT")
    plan_details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

class MCPToolAuditLog(models.Model):
    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('BLOCKED', 'Blocked'),
        ('ERROR', 'Error'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tool_name = models.CharField(max_length=255)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.status}] {self.tool_name} at {self.timestamp}"
