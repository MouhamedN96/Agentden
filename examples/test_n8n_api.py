"""
n8n API Testing Script
Demonstrates how to interact with n8n API for workflow management
"""

import os
import requests
import json
from typing import Dict, List, Any

# Configuration
N8N_INSTANCE_URL = os.getenv("N8N_INSTANCE_URL", "https://par-plays.app.n8n.cloud")
N8N_API_KEY = os.getenv("N8N_API_KEY")

# Remove any trailing paths from instance URL
if "/home" in N8N_INSTANCE_URL:
    N8N_INSTANCE_URL = N8N_INSTANCE_URL.split("/home")[0]

BASE_URL = f"{N8N_INSTANCE_URL}/api/v1"

# Headers for all requests
HEADERS = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json",
    "accept": "application/json"
}


def test_connection():
    """Test API connection"""
    print("Testing n8n API connection...")
    try:
        response = requests.get(f"{BASE_URL}/workflows", headers=HEADERS)
        response.raise_for_status()
        print("✓ Connection successful!")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def list_workflows() -> List[Dict]:
    """List all workflows"""
    print("\nListing workflows...")
    try:
        response = requests.get(f"{BASE_URL}/workflows", headers=HEADERS)
        response.raise_for_status()
        workflows = response.json()
        
        print(f"✓ Found {len(workflows)} workflows:")
        for wf in workflows:
            print(f"  - {wf['name']} (ID: {wf['id']}, Active: {wf['active']})")
        
        return workflows
    except Exception as e:
        print(f"✗ Failed to list workflows: {e}")
        return []


def get_workflow(workflow_id: str) -> Dict:
    """Get workflow details"""
    print(f"\nGetting workflow {workflow_id}...")
    try:
        response = requests.get(f"{BASE_URL}/workflows/{workflow_id}", headers=HEADERS)
        response.raise_for_status()
        workflow = response.json()
        
        print(f"✓ Workflow: {workflow['name']}")
        print(f"  Nodes: {len(workflow.get('nodes', []))}")
        print(f"  Active: {workflow['active']}")
        
        return workflow
    except Exception as e:
        print(f"✗ Failed to get workflow: {e}")
        return {}


def execute_workflow(workflow_id: str, data: Dict = None) -> Dict:
    """Execute a workflow"""
    print(f"\nExecuting workflow {workflow_id}...")
    try:
        payload = {"data": data} if data else {}
        response = requests.post(
            f"{BASE_URL}/workflows/{workflow_id}/execute",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        execution = response.json()
        
        print(f"✓ Execution started: {execution.get('id')}")
        return execution
    except Exception as e:
        print(f"✗ Failed to execute workflow: {e}")
        return {}


def list_executions(workflow_id: str = None) -> List[Dict]:
    """List workflow executions"""
    print("\nListing executions...")
    try:
        url = f"{BASE_URL}/executions"
        if workflow_id:
            url += f"?workflowId={workflow_id}"
        
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        executions = response.json()
        
        print(f"✓ Found {len(executions)} executions:")
        for ex in executions[:5]:  # Show first 5
            print(f"  - {ex['id']}: {ex['status']} ({ex.get('workflowName', 'N/A')})")
        
        return executions
    except Exception as e:
        print(f"✗ Failed to list executions: {e}")
        return []


def get_execution(execution_id: str) -> Dict:
    """Get execution details"""
    print(f"\nGetting execution {execution_id}...")
    try:
        response = requests.get(f"{BASE_URL}/executions/{execution_id}", headers=HEADERS)
        response.raise_for_status()
        execution = response.json()
        
        print(f"✓ Execution: {execution['id']}")
        print(f"  Status: {execution['status']}")
        print(f"  Workflow: {execution.get('workflowName', 'N/A')}")
        
        return execution
    except Exception as e:
        print(f"✗ Failed to get execution: {e}")
        return {}


def create_variable(key: str, value: Any) -> Dict:
    """Create or update a variable"""
    print(f"\nCreating variable {key}...")
    try:
        payload = {
            "key": key,
            "value": json.dumps(value) if not isinstance(value, str) else value
        }
        response = requests.post(f"{BASE_URL}/variables", headers=HEADERS, json=payload)
        response.raise_for_status()
        variable = response.json()
        
        print(f"✓ Variable created: {variable['key']}")
        return variable
    except Exception as e:
        print(f"✗ Failed to create variable: {e}")
        return {}


def list_variables() -> List[Dict]:
    """List all variables"""
    print("\nListing variables...")
    try:
        response = requests.get(f"{BASE_URL}/variables", headers=HEADERS)
        response.raise_for_status()
        variables = response.json()
        
        print(f"✓ Found {len(variables)} variables:")
        for var in variables:
            print(f"  - {var['key']}: {var['value'][:50]}...")
        
        return variables
    except Exception as e:
        print(f"✗ Failed to list variables: {e}")
        return []


def demo_code_on_fly_integration():
    """
    Demonstrate how Code-on-Fly integrates with n8n API
    """
    print("\n" + "="*60)
    print("Code-on-Fly n8n Integration Demo")
    print("="*60)
    
    # 1. Test connection
    if not test_connection():
        print("\n✗ Cannot proceed without API connection")
        return
    
    # 2. List workflows
    workflows = list_workflows()
    
    # 3. Create project context variable
    project_context = {
        "project_id": "demo-project-123",
        "request": "build user authentication",
        "status": "planning",
        "created_at": "2025-12-23T00:00:00Z"
    }
    create_variable("code_on_fly_demo_project", project_context)
    
    # 4. List all variables
    list_variables()
    
    # 5. List recent executions
    list_executions()
    
    print("\n" + "="*60)
    print("Demo complete! n8n API is ready for Code-on-Fly")
    print("="*60)


if __name__ == "__main__":
    # Check if API key is set
    if not N8N_API_KEY:
        print("Error: N8N_API_KEY environment variable not set")
        print("Please set it in your .env file or export it:")
        print("  export N8N_API_KEY=your-api-key")
        exit(1)
    
    # Run demo
    demo_code_on_fly_integration()
    
    # Example usage for specific operations
    print("\n\nExample: How to use in Code-on-Fly")
    print("-" * 60)
    print("""
# Store project context when request comes in
project_context = {
    "project_id": "project-123",
    "request": "build login feature",
    "status": "planning",
    "council_plan": {...},
    "session_id": "session-456"
}
create_variable(f"project_{project_id}", project_context)

# Update status as workflow progresses
project_context["status"] = "implementing"
create_variable(f"project_{project_id}", project_context)

# Execute workflow programmatically
execute_workflow(workflow_id, data={"project_id": project_id})

# Monitor execution
execution = get_execution(execution_id)
print(f"Status: {execution['status']}")
    """)
