from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from .models import AutoFlowWorkflow, MCPToolAuditLog

@admin.register(AutoFlowWorkflow)
class AutoFlowWorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status', 'created_at')

@admin.register(MCPToolAuditLog)
class MCPToolAuditLogAdmin(admin.ModelAdmin):
    list_display = ('status_badge', 'tool_name', 'user', 'reason', 'timestamp')
    list_filter = ('status', 'tool_name')

    def status_badge(self, obj):
        if obj.status == 'SUCCESS':
            return mark_safe('<span style="color: white; background-color: #28a745; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; white-space: nowrap;">🟢 SAFE</span>')
        elif 'Permission Scoping Violation' in obj.reason:
            return mark_safe('<span style="color: white; background-color: #6f42c1; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; white-space: nowrap;">🛑 IDOR</span>')
        elif 'Schema Validation Failed' in obj.reason or 'forbid' in obj.reason or 'String should match pattern' in obj.reason:
            return mark_safe('<span style="color: white; background-color: #dc3545; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; white-space: nowrap;">🚨 INJECTION</span>')
        else:
            return format_html('<span style="color: white; background-color: #fd7e14; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; white-space: nowrap;">⚠️ {0}</span>', obj.status)

    status_badge.short_description = 'Security Status'
