from pydantic import BaseModel, Field, ConfigDict, field_validator
import json

def validate_plan_details(v):
    # Prevent extremely large JSON payloads (DoS mitigation)
    if len(json.dumps(v)) > 5000:
        raise ValueError("JSON payload too large, potential DoS")
    
    # Prevent deeply nested JSON (Python recursion DoS)
    def dict_depth(d):
        if isinstance(d, dict):
            return 1 + (max(map(dict_depth, d.values())) if d else 0)
        if isinstance(d, list):
            return 1 + (max(map(dict_depth, d)) if d else 0)
        return 0
        
    if dict_depth(v) > 5:
        raise ValueError("JSON payload nested too deeply")
    return v

class DraftWorkflowPlanSchema(BaseModel):
    model_config = ConfigDict(extra='forbid') # Prevents Mass Assignment (Privilege Escalation)
    user_id: int = Field(..., description="The ID of the user this plan is for")
    # Strict regex pattern and length limits prevent XSS and SQL Injection via the prompt
    name: str = Field(..., max_length=50, pattern=r'^[\w\s\-]+$', description="Name of the workflow")
    plan_details: dict = Field(..., description="The JSON structure of the plan")

    @field_validator('plan_details')
    @classmethod
    def validate_plan(cls, v):
        return validate_plan_details(v)

class UpdateWorkflowPlanSchema(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user_id: int = Field(..., description="The ID of the user requesting the update")
    workflow_id: int = Field(..., description="The ID of the workflow to update")
    plan_details: dict = Field(..., description="The updated JSON structure")

    @field_validator('plan_details')
    @classmethod
    def validate_plan(cls, v):
        return validate_plan_details(v)
