# AutoFlow: AI-Powered Workflow SaaS (Zero-Trust Architecture)

AutoFlow is a robust, security-first **Web-Based SaaS (Software as a Service)** designed to safely bridge the gap between human users, Large Language Models (LLMs), and server-side database executions. 

By leveraging the **Model Context Protocol (MCP)** natively over HTTP, this project exposes Python backend capabilities to AI agents while ensuring absolute data security and user isolation.

## The Core Concept

Unlike local AI tools, **AutoFlow is a strictly online, web-first platform**. 

1. **Authentication:** Users must go online and sign in via Django Authentication.
2. **The Prompt:** The human user types a prompt into the web application (e.g., *"Create a vacation workflow"*).
3. **The LLM:** The server passes the prompt to an LLM (like Claude or GPT-4).
4. **The Bouncer:** The LLM decides to take action and calls our Django MCP Web API (`/api/mcp/call_tool/`).
5. **The Execution:** Our backend intercepts the LLM's request, mathematically verifies it is safe, and safely updates the database on behalf of the logged-in user.

## Architectural Pillars

- 🛡️ **The Web Bouncer (Middleware)**: Every LLM payload must pass through the `MCPSecurityMiddleware`. It enforces strict **IDOR (Insecure Direct Object Reference) protection**, guaranteeing that an LLM can never alter or access data belonging to a different authenticated user.
- 📏 **The Mathematical Contract (Pydantic)**: Forces the LLM to conform to exact data structures and strict Regular Expressions. This completely neutralizes **Cross-Site Scripting (XSS)**, SQL Injections, and Compute Exhaustion (DoS) attacks before they ever hit the database.
- 📝 **The Immutable Ledger (Observability)**: Every single LLM execution—whether successful or blocked by the Bouncer for containing a prompt injection—is permanently recorded in the `MCPToolAuditLog` table for administrators to review.
- 🧱 **Atomic Transactions**: If the LLM makes a mistake halfway through a complex database operation, Django instantly rolls back the entire transaction to prevent corrupted data fragments.

## Running the Complete Architecture Showcase

This project comes with an interactive script (`showcase.py`) designed to simulate a live LLM interacting with the web Bouncer. Because real LLMs cost money and require API keys, this script visually proves to evaluators that the system intercepts hacks in real-time.

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate   # Windows
   source venv/bin/activate  # Mac/Linux
   ```

2. **Install the dependencies**:
   ```bash
   pip install django mcp pydantic pytest-django requests
   ```

3. **Initialize the database**:
   ```bash
   python manage.py makemigrations core
   python manage.py migrate
   ```

4. **Run the Simulation Script**:
   ```bash
   python showcase.py
   ```
   *Watch the terminal to see exactly how the backend intercepts messy JSON, catches permission hacks, destroys XSS, and handles valid executions.*

5. **View the Web Dashboard (The Proof)**:
   Start your standard Django web server:
   ```bash
   python manage.py runserver
   ```
   Open your browser to [http://localhost:8000/admin](http://localhost:8000/admin).
   - **Username:** `Admin_Alice`
   - **Password:** `password123`
   
   Navigate to the **MCP Tool Audit Logs** table to physically inspect the rows of data showing exactly why the LLM was blocked on each hacking attempt!

## Project Structure & Documentation

*   **`core/views.py`**: The MCP Web API Bridge (`/api/mcp/call_tool/`).
*   **`core/middleware.py`**: The Web Bouncer (IDOR protection).
*   **`core/schemas.py`**: The Mathematical Contract (XSS / SQLi protection).
*   **`core/tools.py`**: The Engine (Atomic database operations).
*   **`core/models.py`**: The Blueprint & Ledger (`AutoFlowWorkflow`, `MCPToolAuditLog`).

**For a deep dive into how this architecture perfectly addresses theoretical concepts, security boundaries, and the master rubric, read the generated [project-explication.md](project-explication.md) file.**
