"""
Test Sandbox Integration
Comprehensive testing script for sandbox service and integration
"""

import os
import requests
import json
import time
from typing import Dict, Any

# Configuration
SANDBOX_SERVICE_URL = os.getenv("SANDBOX_SERVICE_URL", "http://localhost:8003")
CODER_SERVICE_URL = os.getenv("CODER_SERVICE_URL", "http://localhost:8002")


class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_test(name: str):
    """Print test name"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}{Colors.END}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")


# Test 1: Health Checks
def test_health_checks():
    """Test that all services are healthy"""
    print_test("Health Checks")
    
    # Test sandbox service
    try:
        response = requests.get(f"{SANDBOX_SERVICE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "healthy":
            print_success(f"Sandbox service healthy")
            print_info(f"  Active sandboxes: {data['active_sandboxes']}")
            print_info(f"  E2B configured: {data['e2b_configured']}")
        else:
            print_error("Sandbox service unhealthy")
            return False
    except Exception as e:
        print_error(f"Sandbox service unreachable: {e}")
        return False
    
    # Test coder service
    try:
        response = requests.get(f"{CODER_SERVICE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "healthy":
            print_success(f"Coder service healthy")
            print_info(f"  Active sessions: {data['active_sessions']}")
        else:
            print_error("Coder service unhealthy")
            return False
    except Exception as e:
        print_error(f"Coder service unreachable: {e}")
        return False
    
    return True


# Test 2: Sandbox Creation
def test_sandbox_creation():
    """Test creating a sandbox"""
    print_test("Sandbox Creation")
    
    try:
        response = requests.post(
            f"{SANDBOX_SERVICE_URL}/sandbox/create",
            json={
                "environment": "nodejs-18",
                "timeout": 3600
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        sandbox_id = data["sandbox_id"]
        print_success(f"Sandbox created: {sandbox_id}")
        print_info(f"  Status: {data['status']}")
        print_info(f"  Created at: {data['created_at']}")
        
        return sandbox_id
    except Exception as e:
        print_error(f"Failed to create sandbox: {e}")
        return None


# Test 3: Simple Code Execution
def test_code_execution(sandbox_id: str):
    """Test executing simple code in sandbox"""
    print_test("Simple Code Execution")
    
    try:
        response = requests.post(
            f"{SANDBOX_SERVICE_URL}/sandbox/{sandbox_id}/execute",
            json={
                "files": {
                    "hello.js": "console.log('Hello from sandbox!');"
                },
                "commands": ["node hello.js"],
                "timeout": 60
            },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        
        result = data["results"][0]
        
        if result["exit_code"] == 0:
            print_success("Code executed successfully")
            print_info(f"  Output: {result['stdout'].strip()}")
            print_info(f"  Duration: {result['duration']:.2f}s")
            return True
        else:
            print_error(f"Execution failed with exit code {result['exit_code']}")
            print_error(f"  stderr: {result['stderr']}")
            return False
    except Exception as e:
        print_error(f"Failed to execute code: {e}")
        return False


# Test 4: Test Execution
def test_test_execution(sandbox_id: str):
    """Test running tests in sandbox"""
    print_test("Test Execution")
    
    # Create a simple test file
    code = """
function add(a, b) {
    return a + b;
}

module.exports = { add };
"""
    
    test_code = """
const { add } = require('./math');

test('adds 1 + 2 to equal 3', () => {
    expect(add(1, 2)).toBe(3);
});

test('adds -1 + 1 to equal 0', () => {
    expect(add(-1, 1)).toBe(0);
});
"""
    
    package_json = json.dumps({
        "name": "test-project",
        "version": "1.0.0",
        "scripts": {
            "test": "jest"
        },
        "devDependencies": {
            "jest": "^29.0.0"
        }
    }, indent=2)
    
    try:
        response = requests.post(
            f"{SANDBOX_SERVICE_URL}/sandbox/{sandbox_id}/execute",
            json={
                "files": {
                    "math.js": code,
                    "math.test.js": test_code,
                    "package.json": package_json
                },
                "commands": [
                    "npm install",
                    "npm test"
                ],
                "timeout": 300
            },
            timeout=320
        )
        response.raise_for_status()
        data = response.json()
        
        # Check npm install
        install_result = data["results"][0]
        if install_result["exit_code"] == 0:
            print_success("Dependencies installed")
        else:
            print_error("Failed to install dependencies")
            return False
        
        # Check tests
        test_result = data["results"][1]
        if test_result["exit_code"] == 0:
            print_success("Tests passed")
            
            if test_result.get("test_results"):
                tr = test_result["test_results"]
                print_info(f"  Total: {tr['total']}")
                print_info(f"  Passed: {tr['passed']}")
                print_info(f"  Failed: {tr['failed']}")
            
            return True
        else:
            print_error("Tests failed")
            print_error(f"  stderr: {test_result['stderr'][:200]}")
            return False
    except Exception as e:
        print_error(f"Failed to run tests: {e}")
        return False


# Test 5: Sandbox Status
def test_sandbox_status(sandbox_id: str):
    """Test getting sandbox status"""
    print_test("Sandbox Status")
    
    try:
        response = requests.get(
            f"{SANDBOX_SERVICE_URL}/sandbox/{sandbox_id}/status",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        print_success("Got sandbox status")
        print_info(f"  Status: {data['status']}")
        print_info(f"  Uptime: {data['uptime']}s")
        print_info(f"  Executions: {data['executions']}")
        
        return True
    except Exception as e:
        print_error(f"Failed to get status: {e}")
        return False


# Test 6: Sandbox Cleanup
def test_sandbox_cleanup(sandbox_id: str):
    """Test destroying sandbox"""
    print_test("Sandbox Cleanup")
    
    try:
        response = requests.delete(
            f"{SANDBOX_SERVICE_URL}/sandbox/{sandbox_id}",
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        print_success(f"Sandbox destroyed: {sandbox_id}")
        print_info(f"  Total uptime: {data['total_uptime']}s")
        print_info(f"  Total executions: {data['total_executions']}")
        
        return True
    except Exception as e:
        print_error(f"Failed to destroy sandbox: {e}")
        return False


# Test 7: End-to-End Feature Implementation
def test_e2e_implementation():
    """Test complete feature implementation flow"""
    print_test("End-to-End Feature Implementation")
    
    # Create a simple plan
    plan = {
        "plan_id": "test-plan-123",
        "features": [
            {
                "id": "feat-1",
                "category": "Math",
                "description": "Addition function",
                "test_cases": [
                    "Test adding positive numbers",
                    "Test adding negative numbers"
                ],
                "priority": "high"
            }
        ],
        "architecture": "Simple math library",
        "security_requirements": [],
        "performance_targets": {},
        "estimated_complexity": "low"
    }
    
    try:
        # Start implementation
        print_info("Starting implementation...")
        response = requests.post(
            f"{CODER_SERVICE_URL}/code/implement",
            json={
                "plan": plan,
                "project_dir": "test-project",
                "webhook_url": "http://localhost:9999/webhook",  # Dummy webhook
                "max_iterations": 5,
                "environment": "nodejs-18"
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        session_id = data["session_id"]
        sandbox_id = data["sandbox_id"]
        
        print_success(f"Implementation started")
        print_info(f"  Session ID: {session_id}")
        print_info(f"  Sandbox ID: {sandbox_id}")
        
        # Poll for completion
        print_info("Waiting for implementation to complete...")
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                status_response = requests.get(
                    f"{CODER_SERVICE_URL}/code/status/{session_id}",
                    timeout=10
                )
                status_response.raise_for_status()
                status = status_response.json()
                
                print_info(f"  Status: {status['status']} - {status['current_feature']}")
                print_info(f"  Progress: {status['progress']['percentage']:.1f}%")
                
                if status["status"] in ["completed", "failed"]:
                    if status["status"] == "completed":
                        print_success("Implementation completed!")
                        print_info(f"  Git commits: {status['git_commits']}")
                        return True
                    else:
                        print_error("Implementation failed")
                        return False
                
                time.sleep(10)
            except Exception as e:
                print_error(f"Error checking status: {e}")
                break
        
        print_error("Implementation timed out")
        return False
        
    except Exception as e:
        print_error(f"Failed to start implementation: {e}")
        return False


# Test 8: List Sandboxes
def test_list_sandboxes():
    """Test listing all sandboxes"""
    print_test("List Sandboxes")
    
    try:
        response = requests.get(
            f"{SANDBOX_SERVICE_URL}/sandboxes",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        print_success(f"Found {len(data['sandboxes'])} active sandboxes")
        
        for sb in data["sandboxes"]:
            print_info(f"  {sb['sandbox_id']}: {sb['status']} ({sb['environment']})")
        
        return True
    except Exception as e:
        print_error(f"Failed to list sandboxes: {e}")
        return False


# Main test runner
def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Code-on-Fly Sandbox Integration Test Suite")
    print(f"{'='*60}{Colors.END}\n")
    
    results = {}
    
    # Test 1: Health checks
    results["health"] = test_health_checks()
    if not results["health"]:
        print_error("\n❌ Services are not healthy. Aborting tests.")
        return
    
    # Test 2-6: Sandbox operations
    sandbox_id = test_sandbox_creation()
    if sandbox_id:
        results["creation"] = True
        results["execution"] = test_code_execution(sandbox_id)
        results["tests"] = test_test_execution(sandbox_id)
        results["status"] = test_sandbox_status(sandbox_id)
        results["cleanup"] = test_sandbox_cleanup(sandbox_id)
    else:
        results["creation"] = False
        results["execution"] = False
        results["tests"] = False
        results["status"] = False
        results["cleanup"] = False
    
    # Test 7: List sandboxes
    results["list"] = test_list_sandboxes()
    
    # Test 8: End-to-end (optional, takes longer)
    print_info("\nE2E test takes 5-10 minutes. Run it? (y/n)")
    # Uncomment to enable interactive prompt:
    # if input().lower() == 'y':
    #     results["e2e"] = test_e2e_implementation()
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Test Summary")
    print(f"{'='*60}{Colors.END}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{test_name.ljust(20)}: {status}")
    
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}{Colors.END}\n")
    
    if passed == total:
        print_success("🎉 All tests passed! Sandbox integration is working correctly.")
    else:
        print_error(f"⚠️  {total - passed} test(s) failed. Review the output above.")


if __name__ == "__main__":
    run_all_tests()
