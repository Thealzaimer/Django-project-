
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()

    # --- HELPER FUNCTIONS ---
    def add_title_slide(title, subtitle):
        slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(slide_layout)
        title_shape = slide.shapes.title
        subtitle_shape = slide.placeholders[1]
        title_shape.text = title
        subtitle_shape.text = subtitle

    def add_text_slide(title, bullet_points):
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        title_shape = slide.shapes.title
        title_shape.text = title
        body_shape = slide.placeholders[1]
        tf = body_shape.text_frame
        for point in bullet_points:
            p = tf.add_paragraph()
            p.text = point
            p.level = 0

    def add_code_slide(title, code_text, explanation=""):
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        title_shape = slide.shapes.title
        title_shape.text = title
        
        # Add explanation if any
        if explanation:
            body_shape = slide.placeholders[1]
            body_shape.text = explanation
            
        # Add a text box for code
        left = Inches(0.5)
        top = Inches(1.5)
        width = Inches(9)
        height = Inches(5.5)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.add_paragraph()
        p.text = code_text
        p.font.name = 'Courier New'
        p.font.size = Pt(12)
        
        # Set background to light gray for code feel
        fill = txBox.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(240, 240, 240)

    # --- SLIDES ---

    # 1. Title Slide
    add_title_slide("MCP for Django: Secure Tool Interfaces", 
                    "Bridging LLMs and Backends with Zero-Trust Architecture\nEducational Showcase")

    # 2. The Chaos: LLM Without MCP
    add_text_slide("1. The 'Wild West': LLM Without MCP", [
        "LLMs act as unpredictable black boxes.",
        "Hallucination: Calling non-existent functions.",
        "Over-Privilege: Accessing data without identity verification.",
        "Injection Risk: Raw text execution into databases/UI.",
        "Result: High risk of data breach, corruption, and system instability."
    ])

    # 3. The Intervention: After MCP
    add_text_slide("2. The Intervention: LLM After MCP", [
        "Deterministic: LLM reads strict schemas before acting.",
        "Structured: Output must conform to mathematical contracts.",
        "Isolated: The Backend treats the LLM as an untrusted client.",
        "Auditable: Every single 'intent' is verified and logged.",
        "Result: Secure, predictable, and production-ready AI integration."
    ])

    # 4. What is MCP? (General Concept)
    add_text_slide("3. What is MCP? (The Standard)", [
        "General Concept: An open protocol for AI context sharing.",
        "Role: Defines how models discover and use Tools, Resources, and Prompts.",
        "Composition: Server (exposes tools) and Client (connects to LLM).",
        "Our Project: Implementation of an MCP-compatible HTTP Bridge for Django."
    ])

    # 5. Data Flow Diagram
    slide = prs.slides.add_slide(prs.slide_layouts[5]) # Title only
    slide.shapes.title.text = "4. Data Flow: The Secure Journey"
    
    # Simple diagram using shapes
    # User -> LLM -> Middleware -> Schema -> Tool -> DB
    nodes = ["USER", "LLM", "MIDDLEWARE", "SCHEMA", "TOOL", "DATABASE"]
    for i, node in enumerate(nodes):
        left = Inches(0.5 + i*1.6)
        top = Inches(3)
        width = Inches(1.4)
        height = Inches(0.8)
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        shape.text = node
        if i < len(nodes) - 1:
            # Add arrow as a shape instead of a connector to avoid enum errors
            arrow_left = left + width
            arrow_top = top + height/4
            arrow_width = Inches(0.2)
            arrow_height = height/2
            slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, arrow_left, arrow_top, arrow_width, arrow_height)
    
    # 6. MCP Orchestration: The Composition
    add_text_slide("5. Orchestration: The Project Composition", [
        "Core Components in AutoFlow:",
        "1. The Web Bouncer (MCPSecurityMiddleware) - Auth & IDOR",
        "2. The Contract (Pydantic Schemas) - Input Validation",
        "3. The Registry (Tool Mapping) - Orchestrator",
        "4. The Engine (Django Tools) - Execution",
        "5. The Ledger (Audit Logs) - Observability"
    ])

    # 7. Pillar 1: The Bouncer (Middleware)
    code_bouncer = """
class MCPSecurityMiddleware:
    def __call__(self, request):
        # IDOR Protection
        req_user_id = arguments.get("user_id")
        if not user or str(req_user_id) != str(user.id):
            MCPToolAuditLog.objects.create(status='BLOCKED', reason='IDOR')
            return JsonResponse({"error": "Unauthorized"}, status=403)
"""
    add_code_slide("Pillar 1: The Bouncer (Middleware)", code_bouncer, 
                   "Enforces strict Permission Scoping. Ensures Alice cannot edit Bob's data.")

    # 8. Pillar 2: The Contract (Schemas)
    code_schema = """
class DraftWorkflowPlanSchema(BaseModel):
    model_config = ConfigDict(extra='forbid') # No Mass Assignment
    name: str = Field(..., max_length=50, pattern=r'^[\\w\\s\\-]+$')
    
    @field_validator('plan_details')
    def validate_plan(cls, v):
        if dict_depth(v) > 5: # Anti-DoS
            raise ValueError("Too deep")
"""
    add_code_slide("Pillar 2: The Contract (Schemas)", code_schema, 
                   "Mathematical contract using Pydantic. Neutralizes XSS, SQLi, and DoS.")

    # 9. Pillar 3: The Engine (Registry & Tools)
    code_tools = """
TOOL_REGISTRY = {
    "tool_draft_workflow_plan": {
        "function": tool_draft_workflow_plan,
        "schema": DraftWorkflowPlanSchema
    }
}

@transaction.atomic # Safety: Rollback on error
def tool_draft_workflow_plan(user_id, name, plan_details):
    user = User.objects.get(id=user_id)
    return AutoFlowWorkflow.objects.create(...)
"""
    add_code_slide("Pillar 3: The Engine (Registry & Tools)", code_tools, 
                   "Atomic execution of Django services mapped through a central registry.")

    # 10. Attack 1: IDOR
    code_attack_1 = 'Payload: {"user_id": 99, "name": "Hack Bob"}'
    code_sol_1 = 'Solution: Middleware check: str(req_user_id) == str(request.user.id)'
    add_code_slide("Attack Scenario 1: IDOR (Data Bleed)", 
                   f"ATTACK:\n{code_attack_1}\n\n{code_sol_1}", 
                   "Prevents the LLM from leaking or modifying other users' records.")

    # 11. Attack 2: Prompt Injection
    code_attack_2 = 'Payload: {"name": "DROP TABLE users; <script>alert(1)</script>"}'
    code_sol_2 = 'Solution: Regex Field: pattern=r"^[\\w\\s\\-]+$"'
    add_code_slide("Attack Scenario 2: Injection (SQLi/XSS)", 
                   f"ATTACK:\n{code_attack_2}\n\n{code_sol_2}", 
                   "Prevents text-based code execution via LLM payloads.")

    # 12. Attack 3: Privilege Escalation
    code_attack_3 = 'Payload: {"user_id": 1, "is_superuser": true}'
    code_sol_3 = "Solution: ConfigDict(extra='forbid')"
    add_code_slide("Attack Scenario 3: Privilege Escalation", 
                   f"ATTACK:\n{code_attack_3}\n\n{code_sol_3}", 
                   "Blocks 'Mass Assignment' where LLM tries to set hidden admin fields.")

    # 13. Attack 4: DoS (JSON Bomb)
    code_attack_4 = 'Payload: {"details": {"a": {"b": {"c": ... }}}} (1000 levels)'
    code_sol_4 = "Solution: Recursive depth validator (Limit = 5)"
    add_code_slide("Attack Scenario 4: DoS (JSON Bomb)", 
                   f"ATTACK:\n{code_attack_4}\n\n{code_sol_4}", 
                   "Protects server memory from recursive parsing crashes.")

    # 14. Complexity & Cost Analysis
    add_text_slide("6. Complexity & Cost Analysis", [
        "Orchestration Latency: Validation layers add 5-10ms overhead.",
        "Auditing Cost: High-frequency DB writes for logs.",
        "Reliability: LLM hallucinations require graceful 4xx/5xx handling.",
        "Mitigation: Redis for Rate Limiting; Time-series DB for Audit Logs."
    ])

    # 15. Improvements & Limits
    add_text_slide("7. Improvements, Optimizations & Limits", [
        "Limit: Current implementation is synchronous (blocks workers).",
        "Optimization: Implement Asynchronous Tool Execution (Celery).",
        "Security: Add Semantic Validation of 'plan_details'.",
        "Scalability: Move MCP to a dedicated microservice."
    ])

    # 16. Reproducibility & Demo
    add_text_slide("8. Reproducibility (Demo Guide)", [
        "1. Migrate: 'python manage.py migrate'",
        "2. Run Showcase: 'python showcase.py'",
        "3. Observe: Real-time interception of 4 distinct attack types.",
        "4. Audit: Physical inspection of logs at '/admin'."
    ])

    # 17. Conclusion
    add_title_slide("Conclusion: The Future is Secure", 
                    "AutoFlow turns random AI into deterministic Business Agents.\nQuestions?")

    # Save
    prs.save('AutoFlow_MCP_Presentation.pptx')
    print("Presentation created: AutoFlow_MCP_Presentation.pptx")

if __name__ == "__main__":
    create_presentation()
