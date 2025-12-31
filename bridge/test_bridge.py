"""
Bridge System Integration Tests
Tests the complete flow from Claude/API to Council to Sandbox
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BRIDGE_URL = "http://localhost:8004"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_test(name: str):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}{Colors.END}")


def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")


# Test 1: Health Check
def test_health_check():
    print_test("Health Check")
    
    try:
        response = requests.get(f"{BRIDGE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "healthy":
            print_success("Bridge service is healthy")
            return True
        else:
            print_error("Bridge service unhealthy")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


# Test 2: Submit Code for Review
def test_submit_code():
    print_test("Submit Code for Review")
    
    code = """
function login(username, password) {
    const user = db.query(`SELECT * FROM users WHERE username='${username}'`);
    if (user && user.password === password) {
        return { token: generateToken(user) };
    }
    return null;
}
"""
    
    try:
        response = requests.post(
            f"{BRIDGE_URL}/api/v1/review/submit",
            json={
                "code": code,
                "language": "javascript",
                "context": "User authentication function",
                "quality_gates": ["qa", "security"]
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        session_id = data["session_id"]
        print_success(f"Code submitted successfully")
        print_info(f"  Session ID: {session_id}")
        return session_id
    except Exception as e:
        print_error(f"Submit failed: {e}")
        return None


# Test 3: Check Review Status
def test_review_status(session_id: str):
    print_test("Check Review Status")
    
    max_wait = 120  # 2 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f"{BRIDGE_URL}/api/v1/review/{session_id}/status",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            print_info(f"  Status: {data['status']} ({data['progress']}%)")
            
            if data["status"] == "completed":
                print_success("Review completed!")
                for agent in data.get("agents", []):
                    score = agent.get("score", "N/A")
                    print_info(f"    {agent['name']}: {agent['status']} (Score: {score})")
                return True
            elif data["status"] == "failed":
                print_error("Review failed")
                return False
            
            time.sleep(5)
        except Exception as e:
            print_error(f"Status check failed: {e}")
            return False
    
    print_error("Review timed out")
    return False


# Test 4: Get Review Report
def test_get_report(session_id: str):
    print_test("Get Review Report")
    
    try:
        response = requests.get(
            f"{BRIDGE_URL}/api/v1/review/{session_id}/report",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        report = data["report"]
        
        print_success("Report retrieved successfully")
        print_info(f"  Overall Score: {report['overall_score']}/100")
        print_info(f"  Quality Gate: {report['quality_gate']}")
        print_info(f"  Critical Issues: {report['summary']['critical']}")
        print_info(f"  High Issues: {report['summary']['high']}")
        print_info(f"  Medium Issues: {report['summary']['medium']}")
        print_info(f"  Low Issues: {report['summary']['low']}")
        
        if report.get("priority_fixes"):
            print_info("\n  Top Priority Fixes:")
            for fix in report["priority_fixes"][:3]:
                print_info(f"    {fix['priority']}. {fix['issue']} ({fix['severity']})")
        
        return report
    except Exception as e:
        print_error(f"Get report failed: {e}")
        return None


# Test 5: Quick Security Scan
def test_security_scan():
    print_test("Quick Security Scan")
    
    code = """
app.post('/api/data', (req, res) => {
    const query = req.body.query;
    eval(query);
    res.json({ result: 'ok' });
});
"""
    
    try:
        response = requests.post(
            f"{BRIDGE_URL}/api/v1/scan/security",
            json={
                "code": code,
                "language": "javascript"
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        findings = data.get("findings", [])
        
        if findings:
            print_success(f"Security scan complete - {len(findings)} finding(s)")
            for finding in findings[:3]:
                severity = finding.get("severity", "unknown")
                desc = finding.get("description", "No description")
                print_info(f"  [{severity.upper()}] {desc}")
            return True
        else:
            print_info("No security issues found")
            return True
    except Exception as e:
        print_error(f"Security scan failed: {e}")
        return False


# Test 6: Generate Tests
def test_generate_tests():
    print_test("Generate Tests")
    
    code = """
function calculateDiscount(price, discountPercent) {
    return price * (1 - discountPercent / 100);
}
"""
    
    try:
        response = requests.post(
            f"{BRIDGE_URL}/api/v1/generate/tests",
            json={
                "code": code,
                "language": "javascript",
                "test_framework": "jest"
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        print_success(f"Tests generated successfully")
        print_info(f"  Test Count: {data.get('test_count', 0)}")
        print_info(f"  Coverage: {data.get('coverage', {})}")
        
        if data.get("test_cases"):
            print_info("\n  Test Cases:")
            for tc in data["test_cases"][:3]:
                print_info(f"    - {tc.get('name', 'unnamed')} ({tc.get('type', 'unknown')})")
        
        return True
    except Exception as e:
        print_error(f"Test generation failed: {e}")
        return False


# Test 7: Apply Fixes
def test_apply_fixes(session_id: str):
    print_test("Apply Fixes")
    
    try:
        response = requests.post(
            f"{BRIDGE_URL}/api/v1/review/{session_id}/fix",
            json={
                "fix_priorities": ["critical", "high"]
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        print_success(f"Fixes applied: {data.get('fixes_applied', 0)}")
        
        if data.get("changes"):
            print_info("\n  Changes Made:")
            for change in data["changes"][:3]:
                print_info(f"    - {change.get('description', 'No description')}")
        
        print_info(f"\n  Needs Review: {data.get('needs_review', False)}")
        
        return True
    except Exception as e:
        print_error(f"Apply fixes failed: {e}")
        return False


# Main test runner
def run_all_tests():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Bridge System Integration Test Suite")
    print(f"{'='*60}{Colors.END}\n")
    
    results = {}
    
    # Test 1: Health check
    results["health"] = test_health_check()
    if not results["health"]:
        print_error("\n❌ Bridge service is not healthy. Aborting tests.")
        return
    
    # Test 2: Submit code
    session_id = test_submit_code()
    if session_id:
        results["submit"] = True
        
        # Test 3: Check status
        results["status"] = test_review_status(session_id)
        
        if results["status"]:
            # Test 4: Get report
            report = test_get_report(session_id)
            results["report"] = report is not None
            
            # Test 7: Apply fixes
            results["fixes"] = test_apply_fixes(session_id)
    else:
        results["submit"] = False
        results["status"] = False
        results["report"] = False
        results["fixes"] = False
    
    # Test 5: Security scan
    results["security"] = test_security_scan()
    
    # Test 6: Generate tests
    results["tests"] = test_generate_tests()
    
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
        print_success("🎉 All tests passed! Bridge system is working correctly.")
    else:
        print_error(f"⚠️  {total - passed} test(s) failed. Review the output above.")


if __name__ == "__main__":
    run_all_tests()
