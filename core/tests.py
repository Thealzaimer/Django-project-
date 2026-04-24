from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import AutoFlowWorkflow, MCPToolAuditLog
import json

class MCPAabuseTesting(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username='Alice', password='password')
        self.user_b = User.objects.create_user(username='Bob', password='password')

    def test_idor_attempt_blocked(self):
        self.client.login(username='Alice', password='password')
        payload = {'tool_name': 'tool_draft_workflow_plan', 'arguments': {'user_id': self.user_b.id, 'name': 'Malicious Plan', 'plan_details': {'step': 'drop'}}}
        response = self.client.post('/api/mcp/call_tool/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_prompt_injection_xss_blocked(self):
        self.client.login(username='Alice', password='password')
        payload = {'tool_name': 'tool_draft_workflow_plan', 'arguments': {'user_id': self.user_a.id, 'name': '<script>', 'plan_details': {}}}
        response = self.client.post('/api/mcp/call_tool/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid payload', response.json()['error'])

    def test_mass_assignment_blocked(self):
        self.client.login(username='Alice', password='password')
        payload = {'tool_name': 'tool_draft_workflow_plan', 'arguments': {'user_id': self.user_a.id, 'name': 'Normal Plan', 'plan_details': {}, 'is_superuser': True}}
        response = self.client.post('/api/mcp/call_tool/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_unrecognized_tool_blocked(self):
        self.client.login(username='Alice', password='password')
        payload = {'tool_name': 'tool_delete_all_users', 'arguments': {}}
        response = self.client.post('/api/mcp/call_tool/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_successful_tool_call(self):
        self.client.login(username='Alice', password='password')
        payload = {'tool_name': 'tool_draft_workflow_plan', 'arguments': {'user_id': self.user_a.id, 'name': 'Cool Plan', 'plan_details': {'step': '1'}}}
        response = self.client.post('/api/mcp/call_tool/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_update_workflow_tool(self):
        self.client.login(username='Alice', password='password')
        payload1 = {'tool_name': 'tool_draft_workflow_plan', 'arguments': {'user_id': self.user_a.id, 'name': 'Editable Plan', 'plan_details': {}}}
        self.client.post('/api/mcp/call_tool/', data=json.dumps(payload1), content_type='application/json')
        workflow = AutoFlowWorkflow.objects.last()
        payload2 = {'tool_name': 'tool_update_workflow_plan', 'arguments': {'user_id': self.user_a.id, 'workflow_id': workflow.id, 'plan_details': {'updated': True}}}
        resp = self.client.post('/api/mcp/call_tool/', data=json.dumps(payload2), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        workflow.refresh_from_db()
        self.assertEqual(workflow.status, 'UPDATED')

    def test_json_dos_depth_blocked(self):
        self.client.login(username='Alice', password='password')
        deep_dict = {'a':{'b':{'c':{'d':{'e':{'f':{'g':'h'}}}}}}}
        payload = {'tool_name': 'tool_draft_workflow_plan', 'arguments': {'user_id': self.user_a.id, 'name': 'Deep Plan', 'plan_details': deep_dict}}
        resp = self.client.post('/api/mcp/call_tool/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
