import os
import django
import sys

# Setup Django Environment so we can use ORM and tools natively
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoflow.settings')
django.setup()

from mcp.server.fastmcp import FastMCP
from core.tools import tool_draft_workflow_plan, tool_update_workflow_plan
from core.schemas import DraftWorkflowPlanSchema, UpdateWorkflowPlanSchema
from core.models import MCPToolAuditLog
from django.contrib.auth.models import User
from pydantic import ValidationError
import json

# Initialize the official MCP SDK Server
mcp_server = FastMCP("AutoFlow_Django_MCP")

# In a Stdio MCP context, there is no HTTP Session. The server process itself must define the scope.
# We fetch an allowed user context from the environment (e.g., the user running Claude Desktop)
# default to 1 for demonstration if not provided.
AUTHORIZED_USER_ID = int(os.getenv("MCP_AUTHORIZED_USER_ID", 1))

def audit_and_check_auth(tool_name: str, payload: dict, requested_user_id: int):
    """
    Validates permission scoping for the local Stdio MCP server
    and initializes audit logging variables.
    """
    try:
        user = User.objects.get(id=requested_user_id)
    except User.DoesNotExist:
        user = None

    if requested_user_id != AUTHORIZED_USER_ID:
        # IDOR Attempt: LLM is trying to act as a user it is not authorized to be
        MCPToolAuditLog.objects.create(
            user=user,
            tool_name=tool_name,
            payload=payload,
            status="BLOCKED",
            reason=f"Permission Scoping Violation: LLM executed as {AUTHORIZED_USER_ID} but requested {requested_user_id}"
        )
        raise PermissionError(f"Unauthorized: You can only act on behalf of user_id {AUTHORIZED_USER_ID}")

    return user

# We wrap our Django tools to ensure they enforce the exact same Pydantic schemas natively over standard MCP (stdio)
@mcp_server.tool()
def draft_workflow_plan(user_id: int, name: str, plan_details: dict) -> str:
    """Drafts a new workflow plan for a given user."""
    payload = {"user_id": user_id, "name": name, "plan_details": plan_details}
    try:
        user = audit_and_check_auth("draft_workflow_plan", payload, user_id)
        
        # Enforce strict input validation before hitting the DB
        DraftWorkflowPlanSchema(**payload)
        
        result = tool_draft_workflow_plan(user_id, name, plan_details)
        
        if result.get("status") == "success":
            MCPToolAuditLog.objects.create(user=user, tool_name="draft_workflow_plan", payload=payload, status="SUCCESS", reason="Workflow drafted via Stdio")
        else:
            MCPToolAuditLog.objects.create(user=user, tool_name="draft_workflow_plan", payload=payload, status="ERROR", reason=result.get("message"))
            
        return json.dumps(result)
    except PermissionError as e:
        return str(e)
    except ValidationError as e:
        errors = [dict(err) for err in e.errors()]
        for err in errors:
            if 'ctx' in err and 'error' in err['ctx']:
                err['ctx']['error'] = str(err['ctx']['error'])

        MCPToolAuditLog.objects.create(
            user=None,
            tool_name="draft_workflow_plan",
            payload=payload,
            status="BLOCKED",
            reason=f"Schema Validation Failed: {str(e)}"
        )
        return f"Schema Validation Failed (Prompt Injection Blocked): {json.dumps(errors)}"
    except Exception as e:
        MCPToolAuditLog.objects.create(user=None, tool_name="draft_workflow_plan", payload=payload, status="ERROR", reason=str(e))
        return f"Error: {str(e)}"


@mcp_server.tool()
def update_workflow_plan(user_id: int, workflow_id: int, plan_details: dict) -> str:
    """Updates an existing workflow plan."""
    payload = {"user_id": user_id, "workflow_id": workflow_id, "plan_details": plan_details}
    try:
        user = audit_and_check_auth("update_workflow_plan", payload, user_id)
        
        UpdateWorkflowPlanSchema(**payload)
        
        result = tool_update_workflow_plan(user_id, workflow_id, plan_details)
        
        if result.get("status") == "success":
            MCPToolAuditLog.objects.create(user=user, tool_name="update_workflow_plan", payload=payload, status="SUCCESS", reason="Workflow updated via Stdio")
        else:
            MCPToolAuditLog.objects.create(user=user, tool_name="update_workflow_plan", payload=payload, status="ERROR", reason=result.get("message"))
            
        return json.dumps(result)
    except PermissionError as e:
        return str(e)
    except ValidationError as e:
        errors = [dict(err) for err in e.errors()]
        for err in errors:
            if 'ctx' in err and 'error' in err['ctx']:
                err['ctx']['error'] = str(err['ctx']['error'])

        MCPToolAuditLog.objects.create(
            user=None,
            tool_name="update_workflow_plan",
            payload=payload,
            status="BLOCKED",
            reason=f"Schema Validation Failed: {str(e)}"
        )
        return f"Schema Validation Failed (Prompt Injection Blocked): {json.dumps(errors)}"
    except Exception as e:
        MCPToolAuditLog.objects.create(user=None, tool_name="update_workflow_plan", payload=payload, status="ERROR", reason=str(e))
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Start the MCP server natively (Stdio transport). 
    # AI Agents like Claude Desktop will connect via this exact script execution.
    mcp_server.run()