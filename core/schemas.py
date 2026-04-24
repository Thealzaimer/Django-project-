from pydantic import BaseModel, Field

class DraftWorkflowPlanSchema(BaseModel):
    user_id: int = Field(..., description="The ID of the user this plan is for")
    name: str = Field(..., description="Name of the workflow")
    plan_details: dict = Field(..., description="The JSON structure of the plan")

class UpdateWorkflowPlanSchema(BaseModel):
    user_id: int = Field(..., description="The ID of the user requesting the update")
    workflow_id: int = Field(..., description="The ID of the workflow to update")
    plan_details: dict = Field(..., description="The updated JSON structure")
