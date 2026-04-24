# Topic 19: MCP for Django Applications - Project Report

## a) Description
This project implements the Model Context Protocol (MCP) to turn a Django backend into a secure interface for an LLM. It exposes server-side Python capabilities as robust tools while explicitly guaranteeing strict input validation, rigid permission scoping, and complete observability (audit logging) for every single tool invocation.

## b) Theoretical Part
* **MCP Concepts**: The Model Context Protocol (MCP) standardizes how Large Language Models communicate with external data sources and tools. Instead of custom parsing APIs, MCP offers a universal schema allowing LLMs to discover tools, negotiate capabilities, and execute actions on external servers.
* **Tool Schemas**: Tool schemas act as hard mathematical boundaries around an AI's behavior. By leveraging `Pydantic` models, we define the exact JSON arguments an AI is permitted to send. If the AI hallucinates parameters or alters data types, the schema strictly rejects it before code execution.
* **Context Boundaries**: In a stateless LLM environment, context boundaries ensure the agent only interacts with the exact data subset defined by the user session. 
* **Permission Models**: Establishing permissions requires translating a stateless LLM payload into a scoped Django session. This is handled via middleware which intercepts the requested tool action, extracts the `user_id` or target variables from the payload, and validates them against the currently authenticated `request.user`.

## c) Practical Part (Implementation Summary)
A functional Django application was bootstrapped featuring:
- An **`AutoFlowWorkflow`** execution target model.
- An **`MCPToolAuditLog`** model maintaining an immutable ledger of every LLM tool execution.
- Restrictive **Pydantic Tool Contracts** (e.g., `DraftWorkflowPlanSchema`).
- An HTTP-based **MCP Event View** secured by a custom **`MCPSecurityMiddleware`** interceptor.
- A **FastMCP Native Stdio Server** (`mcp_server.py`) with mirrored IDOR security and observability for direct Claude Desktop integration.

## d) Example Plan & Testing 
A rigorous abuse-testing suite was developed utilizing Django's `TestCase` framework (and `showcase.py`) to simulate prompt injections and malicious LLM executions:
1. **IDOR Prevention:** Testing validated that when an LLM requests to alter data for `User B` while operating under `User A`'s context, the middleware blocks the execution and reports an Unauthorized event in the `MCPToolAuditLog`.
2. **Strict Access Control:** An LLM attempting to call an unregistered or destructive tool (`tool_delete_all_users`) is caught by the middleware registry block.
3. **Prompt/Payload Injection:** Bypassing schema fields with excessive string inputs and SQL statements triggered Pydantic validation failures, ensuring no malformed data reaches the ORM logic.
4. **JSON Depth DoS Mitigation:** Testing blocked arbitrarily deep recursive JSON objects (e.g., `plan_details` payload greater than 5 branches deep) preventing server-crashing Memory/Compute Exhaustion loops.

## e) Complexity and Cost Analysis
* **Tool Orchestration Latency:** Exposing tools over HTTP to an LLM introduces serialization/deserialization latency, specifically through JSON parsing and Pydantic validation (usually adding 5–15ms per request). High-volume autonomous AI agents executing massive tool chains could compound this delay, necessitating asynchronous (`async/await`) handling or bulk tool execution.
* **Auditing Overhead:** Every tool invocation triggers a mandatory `INSERT` operation into the `MCPToolAuditLog` table. In large-scale deployments, writing to a relational SQL table for every LLM action can cause database bottlenecks. 
* **Reliability Risk:** System reliability relies heavily on the LLM's adherence to the Tool Schema. Repeated context hallucinations by cheaper models (e.g., passing strings instead of ints) could cause looping errors, draining LLM token limits and computing power.

## f) Improvements, Optimizations, and Limits
* **Improvements for Overhead:** The `MCPToolAuditLog` can be decoupled from the primary PostgreSQL/SQLite database and migrated to a high-throughput time-series database (Redis Streams, Elasticsearch) to avoid dragging down primary ORM queries.
* **Optimizations for Side Effects:** To minimize database fragmentation during tool hallucination, `atomic transaction` blocks (`with transaction.atomic():`) must be enforced around the tool registry. If an LLM executes a complex, multi-step backend orchestration and step 3 fails, steps 1 and 2 automatically roll back, preventing orphan data.
* **System Limits:** Pydantic schema rejection is excellent for data framing, but it lacks semantic understanding. If an LLM correctly structures a payload (e.g., updates workflow name to "dfgjhdfjghdfjg"), the schema passes. Deep semantic validation (e.g., ensuring string values mathematically make contextual sense) remains extremely difficult and fundamentally limits autonomous backend workflows without human-in-the-loop approvals for sensitive data.
