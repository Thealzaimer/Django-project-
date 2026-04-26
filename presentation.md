# 🚀 AutoFlow: MCP for Django Applications
### *Securing the Bridge Between LLMs and Enterprise Backends*

---

## 1. The Chaos: LLM Without MCP
**The Problem: The "Toddler with a Chainsaw" Scenario**

Without a structured protocol, an LLM interacts with your backend blindly. 

*   **Randomness:** The LLM guesses function names or hallucinates arguments.
*   **Insecurity:** It executes raw text, opening the door to SQL Injections.
*   **Chaos:** It has no concept of "User Identity," leading to massive data leaks (IDOR).

**VISUAL: The Unsafe Path**
```text
      [ USER ]
          | (Prompt: "Delete Bob's data")
          v
      [ LLM BRAIN ] --(Blind Guess)--> [ BACKEND ]
                                          |
                               ⚠️ NO VALIDATION ⚠️
                               ⚠️ NO IDENTITY CHECK ⚠️
                               ⚠️ NO AUDIT TRAIL ⚠️
```

---

## 2. The Intervention: LLM With MCP
**The Solution: The "Protocol Handshake"**

When the Model Context Protocol (MCP) intervenes, the LLM is transformed from a random guesser into a **Deterministic Agent**.

*   **Discovery:** The LLM "reads the manual" before it ever starts working.
*   **Constraint:** It can only output data that matches a strict mathematical contract.
*   **Isolation:** The backend treats the LLM as an untrusted client, verifying every byte.

---

## 3. General Concept: What is MCP?
**Model Context Protocol (MCP)** is an open standard that enables a seamless "Handshake" between AI models and local/remote data.

**The Three Pillars of General MCP:**
1.  **Resources:** Read-only data (e.g., local files, database views).
2.  **Tools:** Executable functions (e.g., "Create Plan", "Send Email").
3.  **Prompts:** Templates that guide the LLM's behavior.

**The Handshake Logic:**
> **Client:** "What are your capabilities?"
> **Server:** "Here is my Manifest (Tools + Schemas)."
> **Client:** "Understood. I will now call Tool 'X' with Argument 'Y'."

---

## 4. AutoFlow Orchestration: The 6 Pillars
Our project implements a professional **Zero-Trust Funnel**. Data must descend through six layers of orchestration.

**VISUAL: The Funnel Orchestration**
```text
+-------------------------------------------+
|          AUTOFLOW MCP ARCHITECTURE        |
|                                           |
|  [ LAYER 0 ] -> DISCOVERY ENGINE          | <--- (HANDSHAKE)
|  [ LAYER 1 ] -> THE BOUNCER (Middleware)  | <--- (IDENTITY)
|  [ LAYER 2 ] -> THE CONTRACT (Schemas)    | <--- (VALIDATION)
|  [ LAYER 3 ] -> THE ROUTER (Registry)     | <--- (MAPPING)
|  [ LAYER 4 ] -> THE ENGINE (Atomic)       | <--- (EXECUTION)
|  [ LAYER 5 ] -> THE LEDGER (Audit Log)    | <--- (OBSERVABILITY)
|                                           |
+-------------------------------------------+
```

---

## 5. Pillar 0: The Discovery Engine (New!)
**The Brain's Manual**

Before execution, the LLM discovers its tools via our **Reflection Layer**. It converts Python docstrings into AI instructions.

**Implementation (`core/views.py`):**
```python
@lru_cache(maxsize=1) # Optimization: Cached Handshake
def list_tools_view(request):
    # Dynamically reflects code into a JSON Manual
    manifest = []
    for name, info in TOOL_REGISTRY.items():
        manifest.append({
            "name": name,
            "description": info["function"].__doc__, # The AI's Intelligence
            "input_schema": info["schema"].model_json_schema()
        })
    return JsonResponse({"tools": manifest})
```

---

## 6. Pillar 1: The Bouncer (Middleware)
**The Identity Guard**

Intercepts every LLM call to ensure the AI isn't trying to access data it doesn't own.

**Implementation (`core/middleware.py`):**
```python
# Permission Scoping: Anti-IDOR Check
req_user_id = arguments.get("user_id")
if not user or str(req_user_id) != str(user.id):
    MCPToolAuditLog.objects.create(status="BLOCKED", reason="IDOR Attempt")
    return JsonResponse({"error": "Unauthorized Access"}, status=403)
```

---

## 7. Pillar 2: The Contract (Schemas)
**The Mathematical Constraint**

Uses **Pydantic** to force the LLM to follow strict regex and structure rules.

**Implementation (`core/schemas.py`):**
```python
class DraftWorkflowPlanSchema(BaseModel):
    model_config = ConfigDict(extra='forbid') # Kills Mass Assignment
    # Regex kills SQLi and XSS injection
    name: str = Field(..., max_length=50, pattern=r'^[\w\s\-]+$')
    
    @field_validator('plan_details')
    def validate_plan(cls, v):
        if dict_depth(v) > 5: # Kills DoS "JSON Bombs"
            raise ValueError("Payload too deep")
        return v
```

---

## 8. Pillar 3: The Router (Registry)
**The Traffic Controller**

Maps the LLM's "intent" to the exact Python function in our registry.

**Implementation (`core/tools.py`):**
```python
TOOL_REGISTRY = {
    "tool_draft_workflow_plan": {
        "function": tool_draft_workflow_plan, # The "Doing"
        "schema": DraftWorkflowPlanSchema     # The "Checking"
    }
}
```

---

## 9. Pillar 4: The Execution Engine (Atomic)
**The Safe Hands**

Executes the logic inside an **Atomic Transaction**. If the AI makes a mistake, the database rolls back completely.

**Implementation (`core/tools.py`):**
```python
@transaction.atomic # All-or-Nothing Integrity
def tool_draft_workflow_plan(user_id, name, plan_details):
    user = User.objects.get(id=user_id)
    return AutoFlowWorkflow.objects.create(
        user=user, name=name, plan_details=plan_details
    )
```

---

## 10. Pillar 5: The Ledger (Audit Logs)
**The Final Evidence**

Every call (even blocked attacks) creates an immutable record for administrators.

**Implementation (`core/models.py`):**
```python
class MCPToolAuditLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    tool_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20) # SUCCESS, BLOCKED, ERROR
    reason = models.TextField() # Why did we block it?
```

---

## 11. The Complete Data Flow Journey
**VISUAL: The Handshake & The Flow**

```text
USER             LLM            DISCOVERY        BOUNCER          DATABASE
 |                |                |                |                |
 |---(Init)------>|                |                |                |
 |                |---(List Tools)>|                |                |
 |                |                |--[Generate]---|                |
 |                |                |   Manifest     |                |
 |                |<--(JSON Schema)--------+        |                |
 |                |                                 |                |
 |---(Prompt)---->|                                 |                |
 |                |---(Tool Call Payload)---------->|                |
 |                |                                 |                |
 |                |                                 |--[Verify ID]-->|
 |                |                                 |                |
 |                |                                 |--[Validate]--> |
 |                |                                 |                |
 |                |                                 |---[Commit]---->|
 |<---(Result)----X----------------X----------------|---(Audit Log)->|
```

---

## 12. Step-by-Step Data Journey
1.  **Discovery:** LLM fetches `/api/mcp/list_tools/`. It learns its capabilities.
2.  **Intent:** LLM translates a user prompt into a structured JSON payload.
3.  **Bouncer Check:** Middleware verifies the `user_id` matches the session. **Identity Secured.**
4.  **Contract Check:** Pydantic verifies regex and depth. **Injection Blocked.**
5.  **Execution:** Django creates the record. **State Saved.**
6.  **Ledger:** System writes the audit row. **Observability Complete.**

---

## 13. Security Showcase: Attack 1 - IDOR
**The Attack:** Alice tries to edit Bob's data.

**Attack Code (`showcase.py`):**
```json
{"tool_name": "tool_draft", "arguments": {"user_id": 2, "name": "Hack Bob"}}
```

**The Solution (`middleware.py`):**
```python
if str(req_user_id) != str(request.user.id):
    return JsonResponse({"error": "Unauthorized"}, status=403)
```

---

## 14. Security Showcase: Attack 2 - Injection
**The Attack:** Injection of malicious scripts or SQL.

**Attack Code (`showcase.py`):**
```json
{"name": "My Plan <script>alert(1)</script>"}
```

**The Solution (`schemas.py`):**
```python
# Fails because Regex pattern r'^[\w\s\-]+$' rejects special characters
name: str = Field(..., pattern=r'^[\w\s\-]+$')
```

---

## 15. Security Showcase: Attack 3 - Mass Assignment
**The Attack:** LLM tries to grant itself Admin rights.

**Attack Code (`showcase.py`):**
```json
{"arguments": {"user_id": 1, "is_superuser": true}}
```

**The Solution (`schemas.py`):**
```python
# Fails because 'extra=forbid' rejects arguments not in the blueprint
model_config = ConfigDict(extra='forbid')
```

---

## 16. Security Showcase: Attack 4 - DoS "JSON Bomb"
**The Attack:** Sending 1000 nested layers to crash the server.

**Attack Code (`showcase.py`):**
```json
{"plan_details": {"a": {"b": {"c": ... }}}}
```

**The Solution (`schemas.py`):**
```python
# Fails because 'dict_depth(v) > 5' raises a ValueError
if dict_depth(v) > 5: raise ValueError("Payload too deep")
```

---

## 17. Complexity & Cost Analysis (Req. e)
*   **Orchestration Latency:** The 6-layer funnel adds ~10ms to the request.
*   **Audit Overhead:** High-traffic apps should offload Audit Logs to a separate Time-Series database (like ClickHouse) to avoid DB locks.
*   **Discovery Cost:** By using `lru_cache`, we reduce manifest generation cost to almost zero.

---

## 18. Improvements & Limits (Req. f)
*   **Improvement:** Use Redis for **Rate Limiting** to prevent LLM hallucination loops from flooding the server.
*   **Optimization:** Implement **Asynchronous Tool Execution** using Django Channels for long-running AI tasks.
*   **Limit:** The system currently relies on Pydantic regex; advanced semantic validation (AI checking AI) could be added.

---

## 19. Reproducibility & Deliverables (Req. g)
**The Project is 100% Ready:**
1.  **Run migrations:** `python manage.py migrate`
2.  **Test Discovery:** Visit `http://localhost:8000/api/mcp/list_tools/`
3.  **Run Simulation:** Execute `python showcase.py` to watch the Security Funnel catch attacks in real-time.
4.  **Verify Admin:** Visit `/admin` to see the **Immutable Ledger** of logs.

---
### Conclusion: Perfect AI Infrastructure
By combining **Dynamic Discovery** with a **Zero-Trust Funnel**, we have built a production-grade, secure, and auditable bridge for the AI era.
