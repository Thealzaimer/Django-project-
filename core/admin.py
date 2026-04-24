from django.contrib import admin
from .models import AutoFlowWorkflow, MCPToolAuditLog

@admin.register(AutoFlowWorkflow)
class AutoFlowWorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status', 'created_at')

@admin.register(MCPToolAuditLog)
class MCPToolAuditLogAdmin(admin.ModelAdmin):
    list_display = ('tool_name', 'user', 'status', 'reason', 'timestamp')
    list_filter = ('status', 'tool_name')
