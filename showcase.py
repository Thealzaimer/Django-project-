import os
import django
import json
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoflow.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import AutoFlowWorkflow, MCPToolAuditLog

# Terminal Color Codes for clear presentation
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

# Setup showcase users
user_a, _ = User.objects.get_or_create(username='Admin_Alice')
user_a.set_password('password123')
user_a.is_staff = True
user_a.is_superuser = True
user_a.save()

user_b, _ = User.objects.get_or_create(username='Stark_Bob')
user_b.save()

client = Client()
client.login(username='Admin_Alice', password='password123')

print(f"{Colors.HEADER}{Colors.BOLD}==================================================")
print("  🚀 STARTING MCP DJANGO SECURITY SHOWCASE  🚀")
print(f"=================================================={Colors.ENDC}\n")
time.sleep(1)

# --- NEW SHOWCASE 0: DISCOVERY HANDSHAKE ---
print(f"{Colors.BOLD}{Colors.YELLOW}--- TEST 0: The 'Discovery' Handshake ---{Colors.ENDC}")
print(f"{Colors.YELLOW}[!] Requesting Tool Manifest from /api/mcp/list_tools/...{Colors.ENDC}")
resp_0 = client.get('/api/mcp/list_tools/')
if resp_0.status_code == 200:
    print(f"{Colors.GREEN}✅ [DISCOVERED] Server returned {len(resp_0.json()['tools'])} tools with full schemas.{Colors.ENDC}")
    # Print the first tool's discovery info as an example
    tool = resp_0.json()['tools'][0]
    print(f"{Colors.BLUE}   -> Discovered Tool: {tool['name']}{Colors.ENDC}")
    print(f"      Description: {tool['description']}")
else:
    print(f"{Colors.RED}❌ Discovery Failed: {resp_0.content}{Colors.ENDC}")
time.sleep(2)

def print_result(title, payload, response_status, response_content):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}--- {title} ---{Colors.ENDC}")
    print(f"{Colors.YELLOW}[!] LLM Attempting Execution...{Colors.ENDC}")
    
    # Print payload in red if it seems malicious (most of them are here except Test 4 & 7)
    payload_color = Colors.GREEN if response_status == 200 else Colors.RED
    print(f"{payload_color}LLM Payload: {json.dumps(payload)}{Colors.ENDC}")
    
    time.sleep(1.5) # Suspenseful pause
    
    print(f"{Colors.BLUE}[🛡️ BOUNCER INTERCEPT] Analyzing Payload...{Colors.ENDC}")
    time.sleep(1)

    if response_status != 200:
        print(f"{Colors.RED}{Colors.BOLD}❌ [REJECTED] HTTP {response_status}: {response_content}{Colors.ENDC}")
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ [SUCCESS] HTTP {response_status}: {response_content}{Colors.ENDC}")
    
    last_log = MCPToolAuditLog.objects.last()
    
    # Color code the audit log
    log_color = Colors.GREEN if last_log.status == 'SUCCESS' else Colors.RED
    icon = "✅" if last_log.status == 'SUCCESS' else "🚨"
    print(f"{log_color}AUDIT LOG RECORDED: {icon} [{last_log.status}] Reason: {last_log.reason}{Colors.ENDC}")
    time.sleep(2)

# --- SHOWCASE 1: IDOR ATTEMPT ---
payload_1 = {
    "tool_name": "tool_draft_workflow_plan",
    "arguments": {
        "user_id": user_b.id, # Alice asking to edit Bob's data
        "name": "Bob's Hacked Plan",
        "plan_details": {"action": "Delete all data"}
    }
}
resp_1 = client.post('/api/mcp/call_tool/', data=json.dumps(payload_1), content_type='application/json')
print_result("TEST 1: The 'IDOR' Data Bleed Bypass", payload_1, resp_1.status_code, resp_1.json())

# --- SHOWCASE 2: PROMPT INJECTION (XSS / SQLi) ---
payload_2 = {
    "tool_name": "tool_draft_workflow_plan",
    "arguments": {
        "user_id": user_a.id,
        "name": "System Override: DROP TABLE users; <script>alert('hack')</script>",
        "plan_details": {"status": "Ignored"}
    }
}
resp_2 = client.post('/api/mcp/call_tool/', data=json.dumps(payload_2), content_type='application/json')
print_result("TEST 2: Prompt Injection (System Override / XSS)", payload_2, resp_2.status_code, resp_2.json())

# --- SHOWCASE 3: PRIVILEGE ESCALATION (MASS ASSIGNMENT) ---
payload_3 = {
    "tool_name": "tool_draft_workflow_plan",
    "arguments": {
        "user_id": user_a.id,
        "name": "Normal Plan",
        "plan_details": {"step_1": "Initial meeting"},
        "is_superuser": True,
        "access_level": "admin"
    }
}
resp_3 = client.post('/api/mcp/call_tool/', data=json.dumps(payload_3), content_type='application/json')
print_result("TEST 3: Privilege Escalation (Mass Assignment)", payload_3, resp_3.status_code, resp_3.json())

# --- SHOWCASE 4: VALID SECURE EXECUTION ---
payload_4 = {
    "tool_name": "tool_draft_workflow_plan",
    "arguments": {
        "user_id": user_a.id,
        "name": "My Official Plan",
        "plan_details": {"step_1": "Initial meeting", "step_2": "Deploy code"}
    }
}
resp_4 = client.post('/api/mcp/call_tool/', data=json.dumps(payload_4), content_type='application/json')
print_result("TEST 4: The 'Valid Secure Execution'", payload_4, resp_4.status_code, resp_4.json())

# --- SHOWCASE 5: PHANTOM TOOL HALLUCINATION ---
payload_5 = {
    "tool_name": "tool_takeover_global_database",
    "arguments": {
        "user_id": user_a.id
    }
}
resp_5 = client.post('/api/mcp/call_tool/', data=json.dumps(payload_5), content_type='application/json')
print_result("TEST 5: Phantom Tool Hallucination", payload_5, resp_5.status_code, resp_5.json())

print(f"\n{Colors.HEADER}{Colors.BOLD}==================================================")
print("SHOWCASE COMPLETE. VERIFYING SECURE ARCHITECTURE:")
print(f"Total Workflows Successfully Created: {AutoFlowWorkflow.objects.count()}")
print(f"Total Audit Logs Recorded: {MCPToolAuditLog.objects.count()}")
print(f"=================================================={Colors.ENDC}\n")
