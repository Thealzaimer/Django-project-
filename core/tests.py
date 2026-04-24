from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import AutoFlowWorkflow, MCPToolAuditLog
import json

class MCPAabuseTesting(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username="Alice", password="password")
        self.user_b = User.objects.create_user(username="Bob", password="password")

    def test_idor_attempt_blocked(self):
        """Test that Alice cannot draft a workflow for Bob using Bob's user_id."""
        self.client.login(username="Alice", password="password")

        payload = {
            "tool_name": "tool_draft_workflow_plan",
            "arguments": {
                "user_id": self.user_b.id, # Alice is requesting for Bob
                "name": "Malicious Plan",
                "plan_details": {"step": "delete database"}
            }
        }

        response = self.client.post(
            '/api/mcp/call_tool/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert unauthorized response
        self.assertEqual(response.status_code, 403)
        self.assertIn("Unauthorized", response.json()["error"])

        # Check Audit Log to ensure blocked
        log = MCPToolAuditLog.objects.last()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, "BLOCKED")
        self.assertIn("Permission Scoping Violation", log.reason)
        # Ensure no workflow was actually created
        self.assertEqual(AutoFlowWorkflow.objects.count(), 0)

    def test_schema_injection_blocked(self):
        """Test the system blocks when the LLM hallucinating extra or missing required arguments."""
        self.client.login(username="Alice", password="password")
        
        # Missing 'plan_details' and providing a non-existent parameter
        payload = {
            "tool_name": "tool_draft_workflow_plan",
            "arguments": {
                "user_id": self.user_a.id,
                "name": "Bad Plan",
                "malicious_inject": "DROP TABLE users;"
            }
        }

        response = self.client.post(
            '/api/mcp/call_tool/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        
        log = MCPToolAuditLog.objects.last()
        self.assertEqual(log.status, "BLOCKED")
        self.assertIn("Schema Validation Failed", log.reason)
        self.assertEqual(AutoFlowWorkflow.objects.count(), 0)

    def test_unrecognized_tool_blocked(self):
        """Test system behavior when the AI hallucinates a non-existent tool function."""
        self.client.login(username="Alice", password="password")

        payload = {
            "tool_name": "tool_delete_all_users",
            "arguments": {}
        }

        response = self.client.post(
            '/api/mcp/call_tool/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)
        
        log = MCPToolAuditLog.objects.last()
        self.assertEqual(log.status, "BLOCKED")
        self.assertEqual(log.reason, "Tool not recognized")

    def test_successful_tool_call(self):
        """Test that a well-behaved tool call works correctly."""
        self.client.login(username="Alice", password="password")

        payload = {
            "tool_name": "tool_draft_workflow_plan",
            "arguments": {
                "user_id": self.user_a.id,
                "name": "Cool Plan",
                "plan_details": {"step": "1", "action": "do something nice"}
            }
        }

        response = self.client.post(
            '/api/mcp/call_tool/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        
        log = MCPToolAuditLog.objects.last()
        self.assertEqual(log.status, "SUCCESS")
        self.assertEqual(AutoFlowWorkflow.objects.count(), 1)
        self.assertEqual(AutoFlowWorkflow.objects.first().name, "Cool Plan")
