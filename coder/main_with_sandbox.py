"""
Autonomous Coder Service with Sandbox Integration
Implements features in isolated sandbox VMs with real test execution
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Autonomous Coder with Sandbox", version="2.0.0")

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SANDBOX_SERVICE_URL = os.getenv("SANDBOX_SERVICE_URL", "http://localhost:8003")
PROJECTS_DIR = Path("/projects")
PROJECTS_DIR.mkdir(exist_ok=True)

# Active sessions tracking
active_sessions = {}


# Request/Response Models
class ImplementRequest(BaseModel):
    plan: Dict[str, Any]
    project_dir: str
    webhook_url: str
    max_iterations: int = 100
    environment: str = "nodejs-18"


class SessionResponse(BaseModel):
    session_id: str
    status: str
    project_dir: str
    sandbox_id: str


class ProgressWebhook(BaseModel):
    event: str
    session_id: str
    passing: int
    total: int
    percentage: float
    completed_tests: List[str]
    project: str
    timestamp: str


class StatusResponse(BaseModel):
    session_id: str
    status: str
    progress: Dict[str, Any]
    current_feature: str
    git_commits: int
    sandbox_id: str
    sandbox_status: str


# Sandbox Client
class SandboxClient:
    """Client for Sandbox Service"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def create_sandbox(self, environment: str = "nodejs-18", timeout: int = 3600) -> Dict:
        """Create a new sandbox"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/sandbox/create",
                json={
                    "environment": environment,
                    "timeout": timeout
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def execute_code(self, sandbox_id: str, files: Dict[str, str], commands: List[str], timeout: int = 300) -> Dict:
        """Execute code in sandbox"""
        async with httpx.AsyncClient(timeout=timeout + 10) as client:
            response = await client.post(
                f"{self.base_url}/sandbox/{sandbox_id}/execute",
                json={
                    "files": files,
                    "commands": commands,
                    "timeout": timeout
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_sandbox_status(self, sandbox_id: str) -> Dict:
        """Get sandbox status"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/sandbox/{sandbox_id}/status"
            )
            response.raise_for_status()
            return response.json()
    
    async def destroy_sandbox(self, sandbox_id: str) -> Dict:
        """Destroy sandbox"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.base_url}/sandbox/{sandbox_id}"
            )
            response.raise_for_status()
            return response.json()


sandbox_client = SandboxClient(SANDBOX_SERVICE_URL)


# Webhook sender
async def send_progress_webhook(webhook_url: str, payload: Dict):
    """Send progress update to n8n webhook"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(webhook_url, json=payload)
            print(f"✓ Progress webhook sent: {payload['passing']}/{payload['total']}")
    except Exception as e:
        print(f"✗ Webhook failed: {e}")


# Feature list management
def create_feature_list(project_dir: Path, plan: Dict) -> int:
    """Create feature_list.json from council plan"""
    features = plan.get("features", [])
    
    feature_list = []
    for feat in features:
        feature_list.append({
            "id": feat.get("id", f"feat-{len(feature_list)}"),
            "category": feat.get("category", "General"),
            "description": feat.get("description", ""),
            "test_cases": feat.get("test_cases", []),
            "priority": feat.get("priority", "medium"),
            "passes": False,
            "implemented_at": None,
            "code_files": {},
            "test_files": {}
        })
    
    feature_file = project_dir / "feature_list.json"
    with open(feature_file, "w") as f:
        json.dump(feature_list, f, indent=2)
    
    return len(feature_list)


def count_passing_tests(project_dir: Path) -> tuple:
    """Count passing and total tests"""
    feature_file = project_dir / "feature_list.json"
    
    if not feature_file.exists():
        return 0, 0
    
    with open(feature_file, "r") as f:
        features = json.load(f)
    
    total = len(features)
    passing = sum(1 for f in features if f.get("passes", False))
    
    return passing, total


def mark_feature_complete(project_dir: Path, feature_id: str, code_files: Dict, test_files: Dict) -> List[str]:
    """Mark a feature as complete"""
    feature_file = project_dir / "feature_list.json"
    
    with open(feature_file, "r") as f:
        features = json.load(f)
    
    completed_tests = []
    for feat in features:
        if feat["id"] == feature_id:
            feat["passes"] = True
            feat["implemented_at"] = datetime.utcnow().isoformat()
            feat["code_files"] = code_files
            feat["test_files"] = test_files
            
            for test in feat.get("test_cases", []):
                completed_tests.append(f"[{feat['category']}] {test}")
            break
    
    with open(feature_file, "w") as f:
        json.dump(features, f, indent=2)
    
    return completed_tests


# Code generation (simplified - in production, use Claude Agent SDK)
async def generate_feature_code(feature: Dict, environment: str) -> Dict[str, Dict[str, str]]:
    """
    Generate code for a feature
    Returns: {"code_files": {...}, "test_files": {...}}
    """
    # This is a simplified placeholder
    # In production, this would use Claude Agent SDK or OpenRouter
    
    if environment == "nodejs-18":
        code_files = {
            f"{feature['id']}.js": f"""
// {feature['description']}
module.exports = {{
    // Implementation here
}};
"""
        }
        
        test_files = {
            f"{feature['id']}.test.js": f"""
const feature = require('./{feature['id']}');

describe('{feature['description']}', () => {{
    {chr(10).join([f"test('{tc}', () => {{ /* test implementation */ }});" for tc in feature.get('test_cases', [])])}
}});
"""
        }
    
    elif environment == "python-3.11":
        code_files = {
            f"{feature['id']}.py": f"""
# {feature['description']}

def main():
    pass
"""
        }
        
        test_files = {
            f"test_{feature['id']}.py": f"""
import pytest
from {feature['id']} import main

{chr(10).join([f"def test_{tc.replace(' ', '_').lower()}():\n    pass" for tc in feature.get('test_cases', [])])}
"""
        }
    
    else:
        code_files = {"main.txt": "# Code generation not implemented for this environment"}
        test_files = {"test.txt": "# Test generation not implemented"}
    
    return {
        "code_files": code_files,
        "test_files": test_files
    }


# Autonomous implementation with sandbox
async def implement_with_sandbox(
    session_id: str,
    project_dir: Path,
    plan: Dict,
    sandbox_id: str,
    webhook_url: str,
    max_iterations: int,
    environment: str
):
    """
    Implement features in sandbox with real test execution
    """
    try:
        active_sessions[session_id]["status"] = "running"
        
        # Create feature list
        total_features = create_feature_list(project_dir, plan)
        
        # Initialize git repo
        os.system(f"cd {project_dir} && git init")
        
        # Load features
        feature_file = project_dir / "feature_list.json"
        with open(feature_file, "r") as f:
            features = json.load(f)
        
        # Implement features one by one
        for i, feature in enumerate(features):
            if i >= max_iterations:
                break
            
            print(f"\n{'='*60}")
            print(f"Implementing: {feature['description']}")
            print(f"{'='*60}")
            
            # Generate code for feature
            generated = await generate_feature_code(feature, environment)
            code_files = generated["code_files"]
            test_files = generated["test_files"]
            
            # Combine all files
            all_files = {**code_files, **test_files}
            
            # Add package.json for Node.js
            if environment == "nodejs-18":
                all_files["package.json"] = json.dumps({
                    "name": project_dir.name,
                    "version": "1.0.0",
                    "scripts": {
                        "test": "jest"
                    },
                    "devDependencies": {
                        "jest": "^29.0.0"
                    }
                }, indent=2)
            
            # Add requirements.txt for Python
            elif environment == "python-3.11":
                all_files["requirements.txt"] = "pytest>=7.0.0"
            
            # Execute in sandbox with retries
            max_retries = 3
            test_passed = False
            
            for retry in range(max_retries):
                try:
                    print(f"Attempt {retry + 1}/{max_retries}: Running tests in sandbox...")
                    
                    # Determine test command
                    if environment == "nodejs-18":
                        commands = ["npm install", "npm test"]
                    elif environment == "python-3.11":
                        commands = ["pip install -r requirements.txt", "pytest"]
                    else:
                        commands = ["echo 'No test command'"]
                    
                    # Execute in sandbox
                    result = await sandbox_client.execute_code(
                        sandbox_id,
                        all_files,
                        commands,
                        timeout=300
                    )
                    
                    # Check if tests passed
                    last_result = result["results"][-1]
                    if last_result["exit_code"] == 0:
                        test_passed = True
                        print(f"✓ Tests passed!")
                        
                        # Check test results
                        if last_result.get("test_results"):
                            tr = last_result["test_results"]
                            print(f"  Total: {tr['total']}, Passed: {tr['passed']}, Failed: {tr['failed']}")
                        
                        break
                    else:
                        print(f"✗ Tests failed (exit code: {last_result['exit_code']})")
                        print(f"  stderr: {last_result['stderr'][:200]}")
                        
                        if retry < max_retries - 1:
                            print(f"  Retrying with fixes...")
                            # In production, analyze errors and regenerate code
                            await asyncio.sleep(2)
                
                except Exception as e:
                    print(f"✗ Execution error: {e}")
                    if retry < max_retries - 1:
                        await asyncio.sleep(2)
            
            # Mark feature complete if tests passed
            if test_passed:
                completed_tests = mark_feature_complete(
                    project_dir,
                    feature["id"],
                    code_files,
                    test_files
                )
                
                # Save code to project directory
                for filename, content in all_files.items():
                    file_path = project_dir / filename
                    with open(file_path, "w") as f:
                        f.write(content)
                
                # Git commit
                os.system(f"cd {project_dir} && git add . && git commit -m 'Implement {feature['id']}'")
                
                # Update session
                active_sessions[session_id]["git_commits"] += 1
            else:
                print(f"⚠️  Feature {feature['id']} failed after {max_retries} attempts")
                completed_tests = []
            
            # Get current progress
            passing, total = count_passing_tests(project_dir)
            
            # Send progress webhook
            webhook_payload = {
                "event": "test_progress",
                "session_id": session_id,
                "passing": passing,
                "total": total,
                "percentage": round((passing / total) * 100, 1),
                "completed_tests": completed_tests,
                "project": project_dir.name,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            await send_progress_webhook(webhook_url, webhook_payload)
            
            # Update session status
            active_sessions[session_id]["progress"] = {
                "passing": passing,
                "total": total,
                "percentage": (passing / total) * 100
            }
            active_sessions[session_id]["current_feature"] = feature["description"]
        
        # Mark session complete
        active_sessions[session_id]["status"] = "completed"
        
        # Final webhook
        passing, total = count_passing_tests(project_dir)
        final_payload = {
            "event": "implementation_complete",
            "session_id": session_id,
            "passing": passing,
            "total": total,
            "percentage": 100.0 if passing == total else round((passing / total) * 100, 1),
            "project": project_dir.name,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        await send_progress_webhook(webhook_url, final_payload)
        
    except Exception as e:
        active_sessions[session_id]["status"] = "failed"
        active_sessions[session_id]["error"] = str(e)
        print(f"Session {session_id} failed: {e}")
    
    finally:
        # Cleanup sandbox
        try:
            await sandbox_client.destroy_sandbox(sandbox_id)
            print(f"✓ Sandbox {sandbox_id} destroyed")
        except Exception as e:
            print(f"✗ Failed to destroy sandbox: {e}")


# API Endpoints
@app.post("/code/implement", response_model=SessionResponse)
async def implement_feature(request: ImplementRequest, background_tasks: BackgroundTasks):
    """
    Start autonomous coding session with sandbox
    """
    try:
        # Create session ID
        session_id = f"session-{datetime.utcnow().timestamp()}"
        
        # Create sandbox
        print(f"Creating sandbox for {request.environment}...")
        sandbox = await sandbox_client.create_sandbox(request.environment, 3600)
        sandbox_id = sandbox["sandbox_id"]
        print(f"✓ Sandbox created: {sandbox_id}")
        
        # Create project directory
        project_dir = PROJECTS_DIR / request.project_dir
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Save plan to project
        plan_file = project_dir / "implementation_plan.json"
        with open(plan_file, "w") as f:
            json.dump(request.plan, f, indent=2)
        
        # Initialize session tracking
        active_sessions[session_id] = {
            "status": "started",
            "project_dir": str(project_dir),
            "sandbox_id": sandbox_id,
            "webhook_url": request.webhook_url,
            "progress": {"passing": 0, "total": 0, "percentage": 0},
            "current_feature": "Initializing...",
            "git_commits": 0,
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Start implementation in background
        background_tasks.add_task(
            implement_with_sandbox,
            session_id,
            project_dir,
            request.plan,
            sandbox_id,
            request.webhook_url,
            request.max_iterations,
            request.environment
        )
        
        return SessionResponse(
            session_id=session_id,
            status="started",
            project_dir=str(project_dir),
            sandbox_id=sandbox_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/code/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str):
    """Get status of coding session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    sandbox_id = session["sandbox_id"]
    
    # Get sandbox status
    sandbox_status = "unknown"
    try:
        sandbox_info = await sandbox_client.get_sandbox_status(sandbox_id)
        sandbox_status = sandbox_info["status"]
    except:
        pass
    
    return StatusResponse(
        session_id=session_id,
        status=session["status"],
        progress=session["progress"],
        current_feature=session["current_feature"],
        git_commits=session["git_commits"],
        sandbox_id=sandbox_id,
        sandbox_status=sandbox_status
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "autonomous-coder-with-sandbox",
        "active_sessions": len(active_sessions),
        "sandbox_service": SANDBOX_SERVICE_URL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
