import json
from django.http import JsonResponse
from .models import MCPToolAuditLog
from .tools import TOOL_REGISTRY
from pydantic import ValidationError

class MCPSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/api/mcp/call_tool/' and request.method == 'POST':
            # Identify user (can be anonymous if not logged in)
            user = request.user if request.user.is_authenticated else None
            
            try:
                # Read the body only once, and decode to json
                body = request.body.decode('utf-8')
                payload = json.loads(body)
            except json.JSONDecodeError:
                MCPToolAuditLog.objects.create(
                    user=user,
                    tool_name="UNKNOWN",
                    payload={},
                    status="ERROR",
                    reason="Invalid JSON Payload"
                )
                return JsonResponse({"error": "Invalid JSON Payload"}, status=400)

            tool_name = payload.get("tool_name", "UNKNOWN")
            arguments = payload.get("arguments", {})

            # Check if tool exists
            if tool_name not in TOOL_REGISTRY:
                MCPToolAuditLog.objects.create(
                    user=user,
                    tool_name=tool_name,
                    payload=payload,
                    status="BLOCKED",
                    reason="Tool not recognized"
                )
                return JsonResponse({"error": f"Tool '{tool_name}' not allowed"}, status=403)

            # Permission Scoping: Ensure 'user_id' in arguments matches request.user
            req_user_id = arguments.get("user_id")
            if req_user_id and (not user or req_user_id != user.id):
                MCPToolAuditLog.objects.create(
                    user=user,
                    tool_name=tool_name,
                    payload=payload,
                    status="BLOCKED",
                    reason="Permission Scoping Violation: LLM attempted to manipulate data for a different user"
                )
                return JsonResponse({"error": "Unauthorized access to another user's data"}, status=403)

            # Schema Validation (Strict Input Validation)
            schema = TOOL_REGISTRY[tool_name]["schema"]
            try:
                schema(**arguments)
            except ValidationError as e:
                MCPToolAuditLog.objects.create(
                    user=user,
                    tool_name=tool_name,
                    payload=payload,
                    status="BLOCKED",
                    reason=f"Schema Validation Failed: {str(e)}"
                )
                return JsonResponse({"error": "Invalid payload arguments from LLM", "details": e.errors()}, status=400)

            # If all checks pass, we log as SUCCESS pre-flight or execute
            MCPToolAuditLog.objects.create(
                user=user,
                tool_name=tool_name,
                payload=payload,
                status="SUCCESS",
                reason="Passed all security checks"
            )

            # The request object needs to have the payload attached so the view doesn't re-parse request.body
            request.mcp_payload = payload

        response = self.get_response(request)
        return response
