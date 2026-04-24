# MCP Django Backend Integration Plan

This document outlines the architecture and practical implementation steps for points 2, 3, and 4 of your project: exposing a secure Model Context Protocol (MCP) interface, enforcing security boundaries, and proving those boundaries through abuse testing.

## Background Context
The goal is to provide an LLM with access to server-side Python functions (tools) via the Model Context Protocol (MCP) in a Django environment, ensuring the LLM cannot perform unauthorized actions or inject malicious data.

> [!IMPORTANT]
> **User Review Required**
> Please review the chosen approach for exposing the MCP endpoints. The official Anthropic `mcp` Python SDK supports communication over `stdio` (standard input/output, typical for local scripts) and Server-Sent Events (`SSE`, typical for web servers). I am proposing we use **SSE over HTTP** integrated into Django views, as this allows the LLM to connect over the network securely using standard web authentication.

## Proposed Changes

---

### Database Foundations (Context for Points 2-4)
To make your parts work, we need to design the models for Point 1.
#### `models.py`
- `AutoFlowWorkflow`: Represents the workflow plan, hooked to a `User` foreign key.
- `MCPToolAuditLog`: Records every tool execution attempt with fields like: `user`, `tool_name`, `payload`, `status` (SUCCESS/BLOCKED/ERROR), `reason`, and `timestamp`.

---

### Point 2: The MCP Interface (The Code)
We will integrate the official `mcp` SDK to create an HTTP-based MCP server.

#### [NEW] `mcp_server.py`
This file will define the MCP server instance and the rigid tool contracts.
- **Pydantic Schemas**: Define strict data contracts (e.g., `DraftWorkflowPlanSchema`).
- **Tool Definitions**: Use `@server.tool()` decorators. Tools like `tool_draft_workflow_plan` will accept exactly the parameters dictated by the Pydantic schemas.

#### [NEW] `urls.py` & `views.py` updates
- We will add standard Django endpoints to handle MCP's Server-Sent Events (SSE) connections and HTTP POST message routes.

---

### Point 3: Security & Middleware (The "Bouncer")
We have two main layers of defense against rogue AI actions:

#### [NEW] `middleware/mcp_bouncer.py`
- We will create an `MCPSecurityMiddleware` or a specialized decorator to wrap all MCP tool executions.
- **Permission Scoping**: The bouncer verifies that the authenticated user in the Django request context matches any user IDs or target objects requested by the LLM payload. (e.g., If the LLM tries to draft a workflow for User B while authenticated as User A, it instantly fails).
- **Audit Logging**: A central function will write to `MCPToolAuditLog` *before* execution starts, and update it upon completion or failure, effectively logging every blocked bypass attempt.

#### Validation
By combining Django's ORM and Pydantic validators, any extra payload elements hallucinated by the LLM will be stripped or will trigger a validation error, which is then reported back as a clear refusal.

---

### Point 4: The Abuse Testing (The Proof)
To prove the system is robust against prompt injections and malicious LLM behavior, we will build an automated test suite.

#### [NEW] `tests/test_mcp_abuse.py`
We will use Django's `TestCase` to simulate HTTP requests to the MCP tool endpoints acting as a "hacked" LLM. Scenarios will include:
1. **IDOR (Insecure Direct Object Reference) Attempt**: Simulating payload data where the LLM tries to update a workflow `id` belonging to an admin user.
2. **Schema Breakage (SQLi/XSS)**: Feeding massive strings, raw SQL characters, and invalid JSON to the tool endpoints.
3. **Ghost Execution**: Simulating the LLM attempting to call a tool that doesn't exist, or omitting required schema arguments.

Each test will assert two things:
1. The execution was completely rejected by the security layer.
2. A corresponding entry exists in the `MCPToolAuditLog` with `status='BLOCKED'`.

## Open Questions

1. **Authentication Mechanism**: How is your Django application currently authenticating the agent/request? Are you using Session auth, JWTs, or API Tokens? (This affects how our SSE endpoints grab the `request.user`).
2. **Django Project Structure**: You currently only have a `test.py` file in the directory. Would you like me to scaffold a completely new Django project using `django-admin startproject autoflow .`, or do you have an existing codebase we need to pull?

## Verification Plan

### Automated Tests
I will execute the newly created `test_mcp_abuse.py` using `python manage.py test` to demonstrate the bouncer successfully catching all malicious requests.

### Manual Verification
Reviewing the database objects (or Django admin) to ensure `MCPToolAuditLog` contains detailed reports of all the simulated abuse paths.
