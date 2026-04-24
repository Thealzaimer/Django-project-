from typing import Dict, Any
from .models import AutoFlowWorkflow
from django.contrib.auth.models import User
import json

def tool_draft_workflow_plan(user_id: int, name: str, plan_details: dict) -> Dict[str, Any]:
    try:
        user = User.objects.get(id=user_id)
        workflow = AutoFlowWorkflow.objects.create(
            user=user,
            name=name,
            plan_details=plan_details,
            status="DRAFT"
        )
        return {"status": "success", "message": "Workflow drafted successfully", "workflow_id": workflow.id}
    except User.DoesNotExist:
        return {"status": "error", "message": "User not found"}

def tool_update_workflow_plan(user_id: int, workflow_id: int, plan_details: dict) -> Dict[str, Any]:
    try:
        workflow = AutoFlowWorkflow.objects.get(id=workflow_id, user_id=user_id)
        workflow.plan_details = plan_details
        workflow.status = "UPDATED"
        workflow.save()
        return {"status": "success", "message": "Workflow updated successfully", "workflow_id": workflow.id}
    except AutoFlowWorkflow.DoesNotExist:
        return {"status": "error", "message": "Workflow not found or does not belong to user"}

# Registry to map tool names to functions and Pydantic schemas
from .schemas import DraftWorkflowPlanSchema, UpdateWorkflowPlanSchema

TOOL_REGISTRY = {
    "tool_draft_workflow_plan": {
        "function": tool_draft_workflow_plan,
        "schema": DraftWorkflowPlanSchema
    },
    "tool_update_workflow_plan": {
        "function": tool_update_workflow_plan,
        "schema": UpdateWorkflowPlanSchema
    }
}
