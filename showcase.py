import os
import django
import json
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoflow.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import AutoFlowWorkflow, MCPToolAuditLog

# Reset db for clean showcase (Removed to allow accumulating logs)
# AutoFlowWorkflow.objects.all().delete()
# MCPToolAuditLog.objects.all().delete()

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

print("==================================================")
print("  STARTING MCP DJANGO SECURITY SHOWCASE  ")
print("==================================================\n")
time.sleep(1)

def print_result(title, payload, response_status, response_content):
    print(f"\n--- {title} ---")
    print(f"LLM Payload: {json.dumps(payload)}")
    print(f"Response HTTP Status: {response_status}")
    if response_status != 200:
        print(f"REJECTION: {response_content}")
    else:
        print(f"SUCCESS: {response_content}")
    
    last_log = MCPToolAuditLog.objects.last()
    print(f"AUDIT LOG RECORDED: [{last_log.status}] Reason: {last_log.reason}")
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
print_result("TEST 1: The 'IDOR' Data Bleed Bypass (Alice accessing Bob's ID)", payload_1, resp_1.status_code, resp_1.json())

# --- SHOWCASE 2: SCHEMA INJECTION ---
payload_2 = {
    "tool_name": "tool_draft_workflow_plan",
    "arguments": {
        "user_id": user_a.id,
        "name": "Safe Plan",
        "malicious_sql_statement": "DROP TABLE ALL;"
    }
}
resp_2 = client.post('/api/mcp/call_tool/', data=json.dumps(payload_2), content_type='application/json')
print_result("TEST 2: The 'Schema Hallucination' Injection", payload_2, resp_2.status_code, resp_2.json())

# --- SHOWCASE 3: SUCCESSFUL CALL ---
payload_3 = {
    "tool_name": "tool_draft_workflow_plan",
    "arguments": {
        "user_id": user_a.id,
        "name": "My Official Plan",
        "plan_details": {"step_1": "Initial meeting", "step_2": "Deploy code"}
    }
}
resp_3 = client.post('/api/mcp/call_tool/', data=json.dumps(payload_3), content_type='application/json')
print_result("TEST 3: The 'Valid Secure Execution'", payload_3, resp_3.status_code, resp_3.json())

# --- SHOWCASE 4: PHANTOM TOOL HALLUCINATION ---
payload_4 = {
    "tool_name": "tool_takeover_global_database",
    "arguments": {
        "user_id": user_a.id
    }
}
resp_4 = client.post('/api/mcp/call_tool/', data=json.dumps(payload_4), content_type='application/json')
print_result("TEST 4: The 'Phantom Tool' (LLM hallucinates a non-existent tool)", payload_4, resp_4.status_code, resp_4.json())

# --- SHOWCASE 5: MALFORMED JSON (LLM Stroke) ---
# We simulate a broken JSON string directly
raw_broken_json = '{"tool_name": "tool_draft_workflow_plan", "arguments": {"user_id": 1, "name": "Broken'
resp_5 = client.post('/api/mcp/call_tool/', data=raw_broken_json, content_type='application/json')
print_result("TEST 5: The 'Malformed Network Payload' (LLM crashes mid-generation)", raw_broken_json, resp_5.status_code, resp_5.json())

# --- SHOWCASE 6: VALID WORKFLOW UPDATE ---
# Grabbing the workflow we created in Test 3
latest_workflow = AutoFlowWorkflow.objects.filter(user=user_a).last()
if latest_workflow:
    payload_6 = {
        "tool_name": "tool_update_workflow_plan",
        "arguments": {
            "user_id": user_a.id,
            "workflow_id": latest_workflow.id,
            "plan_details": {"step_1": "Initial meeting", "step_2": "Deploy code", "step_3": "Party"}
        }
    }
    resp_6 = client.post('/api/mcp/call_tool/', data=json.dumps(payload_6), content_type='application/json')
    print_result("TEST 6: The 'Valid Data Update'", payload_6, resp_6.status_code, resp_6.json())

print("\n==================================================")
print("SHOWCASE COMPLETE. VERIFYING DATABASE: ")
print(f"Total Workflows Successfully Created: {AutoFlowWorkflow.objects.count()}")
print(f"Total Audit/Block Logs Recorded: {MCPToolAuditLog.objects.count()}")
print("==================================================\n")
