# AutoFlow: MCP Django Security Interface

AutoFlow is a robust, security-first Django backend designed to safely bridge the gap between Large Language Models (LLMs) and server-side code execution. By leveraging the **Model Context Protocol (MCP)**, this project exposes Python capabilities natively as tools to AI agents, while an active middleware "Bouncer" enforces mathematically rigid data schemas and strict user-level permissions.

## Core Features

- 🛡️ **Zero-Trust Security Middleware (`MCPSecurityMiddleware`)**: Intercepts MCP HTTP payloads to ensure the LLM never alters or accesses data for standard users outside of the authenticated session.
- 📏 **Strict Pydantic Contracts**: Forces LLMs to conform to exact data structures and types, completely neutralizing SQL injections, unpredictable formatting, or missing arguments.
- 📝 **Comprehensive Audit Logging (`MCPToolAuditLog`)**: Enforces total observability by recording every successful execution and every intercepted malicious attempt (e.g., IDOR attempts, hallucinations).
- ⚙️ **Automated Abuse Simulation Suite**: Includes a dedicated testing harness (`showcase.py`) to actively fire prompt injection payloads and permission traversal attempts into the backend to definitively prove the shield works.

## Setup & Installation

Follow these steps to set the project up on your local machine:

1. **Clone the repository and enter the directory**:
   ```bash
   cd "DJANGO PROJECT"
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install django mcp pydantic pytest-django requests
   ```

4. **Initialize the database**:
   ```bash
   python manage.py makemigrations core
   python manage.py migrate
   ```

## Running the Complete Architecture Showcase

This project comes with an interactive script (`showcase.py`) designed to simulate an actual LLM connecting to the backend. It fires **6 different scenarios** at the backend, including hacking attempts, schema breaks, and successful valid updates.

1. **Run the Simulation Script**:
   Ensure your virtual environment is active, then run:
   ```bash
   python showcase.py
   ```
   *Watch the terminal to see exactly how the backend intercepts the messy JSON and handles valid executions.*

2. **View the Web Dashboard (The Proof)**:
   In one terminal, start your standard Django web server:
   ```bash
   python manage.py runserver
   ```
   Open your browser to [http://localhost:8000/admin](http://localhost:8000/admin).
   - **Username:** `Admin_Alice`
   - **Password:** `password123`
   
   Navigate to the **Mcp tool audit logs** table to physically inspect the rows of data showing exactly why the LLM was blocked on each hacking attempt!

## Project Structure

- `core/models.py`: Database models for `AutoFlowWorkflow` and `MCPToolAuditLog`.
- `core/schemas.py`: Pydantic definitions strictly commanding what JSON args the LLM can use.
- `core/tools.py`: The actual backend functions (the tools) that generate or update workflows.
- `core/middleware.py`: The "Bouncer". Handles IDOR prevention and JSON schema validation.
- `showcase.py`: A visual command-line script simulating a live LLM session hitting the Bouncer. 

## Documentation
For further reading on the design decisions regarding latency overhead, orchestration costs, and the limits of Pydantic validation boundaries, please refer to the attached `mcp_django_report.md` and `architecture_presentation.md` files.
