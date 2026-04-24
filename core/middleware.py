import json
import time
from django.http import JsonResponse
from .models import MCPToolAuditLog
from .tools import TOOL_REGISTRY
from pydantic import ValidationError

# A very simple, native in-memory rate limiter to prevent LLM Hallucinated DDoS
# In production, this would use Redis.
RATE_LIMIT_CACHE = {}
MAX_REQUESTS_PER_SECOND = 5

class MCPSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/api/mcp/call_tool/' and request.method == 'POST':
            user = request.user if request.user.is_authenticated else None
            
            # --- Auditing Overhead Mitigation: Rate Limiting ---
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            current_time = time.time()
            if client_ip not in RATE_LIMIT_CACHE:
                RATE_LIMIT_CACHE[client_ip] = []
            
            # Clean up old tracking data (keep only last 1 second)
            RATE_LIMIT_CACHE[client_ip] = [t for t in RATE_LIMIT_CACHE[client_ip] if current_time - t < 1]
            
            if len(RATE_LIMIT_CACHE[client_ip]) >= MAX_REQUESTS_PER_SECOND:
                # We drop the request immediately without logging to DB, protecting it from DDoS overhead
                return JsonResponse({"error": "Rate limit exceeded. LLM is looping/hallucinating."}, status=429)
            
            RATE_LIMIT_CACHE[client_ip].append(current_time)
            # ---------------------------------------------------

            try:
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

            # Permission Scoping: Ensure 'user_id' in arguments exactly matches request.user
            req_user_id = arguments.get("user_id")
            if not user or not req_user_id or str(req_user_id) != str(user.id):
                MCPToolAuditLog.objects.create(
                    user=user,
                    tool_name=tool_name,
                    payload=payload,
                    status="BLOCKED",
                    reason="Permission Scoping Violation: LLM attempted to manipulate data for a different user or missed authentication"
                )
                return JsonResponse({"error": "Unauthorized access to another user's data or missing auth"}, status=403)

            # Schema Validation (Strict Input Validation)
            schema = TOOL_REGISTRY[tool_name]["schema"]
            try:
                schema(**arguments)
            except ValidationError as e:
                # Need to convert Pydantic exceptions properly to dicts so JsonResponse doesn't crash on ValueError
                errors = []
                for err in e.errors():
                    err_dict = dict(err)
                    if 'ctx' in err_dict and 'error' in err_dict['ctx']:
                        err_dict['ctx']['error'] = str(err_dict['ctx']['error'])
                    errors.append(err_dict)

                MCPToolAuditLog.objects.create(
                    user=user,
                    tool_name=tool_name,
                    payload=payload,
                    status="BLOCKED",
                    reason=f"Schema Validation Failed: {str(e)}"
                )
                return JsonResponse({"error": "Invalid payload arguments from LLM", "details": errors}, status=400)

            # The request object needs to have the payload attached so the view doesn't re-parse request.body
            request.mcp_payload = payload

        response = self.get_response(request)
        
        # Post-Execution Audit Logging
        if request.path == '/api/mcp/call_tool/' and request.method == 'POST' and hasattr(request, 'mcp_payload'):
            payload = request.mcp_payload
            tool_name = payload.get("tool_name", "UNKNOWN")
            user = request.user if request.user.is_authenticated else None
            
            if response.status_code == 200:
                MCPToolAuditLog.objects.create(
                    user=user,
                    tool_name=tool_name,
                    payload=payload,
                    status="SUCCESS",
                    reason="Tool executed successfully"
                )
            else:
                try:
                    resp_data = json.loads(response.content)
                    err_msg = resp_data.get("error", "Execution failed")
                except:
                    err_msg = "Execution failed"
                MCPToolAuditLog.objects.create(
                    user=user,
                    tool_name=tool_name,
                    payload=payload,
                    status="ERROR",
                    reason=f"Tool Execution Error: {err_msg}"
                )

        return response
