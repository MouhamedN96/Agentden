"""
Sandbox Service - VM Orchestration for Code Execution
Integrates with E2B for secure, isolated code execution environments
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Sandbox Service", version="1.0.0")

# Configuration
E2B_API_KEY = os.getenv("E2B_API_KEY")
E2B_BASE_URL = "https://api.e2b.dev"

# Active sandboxes tracking
active_sandboxes = {}


# Request/Response Models
class SandboxCreateRequest(BaseModel):
    environment: str = "nodejs-18"  # nodejs-18, python-3.11, go-1.21, etc.
    timeout: int = 3600  # seconds
    resources: Optional[Dict[str, int]] = None


class SandboxResponse(BaseModel):
    sandbox_id: str
    status: str
    connection: Optional[Dict[str, str]] = None
    created_at: str


class ExecuteRequest(BaseModel):
    files: Dict[str, str]  # filename -> content
    commands: List[str]
    timeout: int = 300  # seconds


class CommandResult(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    test_results: Optional[Dict[str, Any]] = None


class ExecuteResponse(BaseModel):
    execution_id: str
    status: str
    results: List[CommandResult]


class SandboxStatus(BaseModel):
    sandbox_id: str
    status: str
    uptime: int
    resources: Dict[str, Any]
    executions: int


class SnapshotRequest(BaseModel):
    name: str


class SnapshotResponse(BaseModel):
    snapshot_id: str
    size: int
    created_at: str


class RestoreRequest(BaseModel):
    snapshot_id: str


# E2B API Client
class E2BClient:
    """Client for E2B API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = E2B_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_sandbox(self, template: str = "base", timeout: int = 3600) -> Dict:
        """Create a new sandbox"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/sandboxes",
                    headers=self.headers,
                    json={
                        "template": template,
                        "timeout": timeout
                    }
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error creating sandbox: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to create sandbox: {str(e)}")
    
    async def execute_code(self, sandbox_id: str, code: str, language: str = "bash") -> Dict:
        """Execute code in sandbox"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/sandboxes/{sandbox_id}/execute",
                    headers=self.headers,
                    json={
                        "code": code,
                        "language": language
                    }
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error executing code: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to execute code: {str(e)}")
    
    async def write_file(self, sandbox_id: str, path: str, content: str) -> Dict:
        """Write file to sandbox"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/sandboxes/{sandbox_id}/files",
                    headers=self.headers,
                    json={
                        "path": path,
                        "content": content
                    }
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error writing file: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")
    
    async def read_file(self, sandbox_id: str, path: str) -> str:
        """Read file from sandbox"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/sandboxes/{sandbox_id}/files/{path}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()["content"]
            except Exception as e:
                print(f"Error reading file: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
    
    async def delete_sandbox(self, sandbox_id: str) -> Dict:
        """Delete sandbox"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.delete(
                    f"{self.base_url}/sandboxes/{sandbox_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return {"status": "deleted"}
            except Exception as e:
                print(f"Error deleting sandbox: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to delete sandbox: {str(e)}")
    
    async def get_sandbox_info(self, sandbox_id: str) -> Dict:
        """Get sandbox information"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/sandboxes/{sandbox_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error getting sandbox info: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get sandbox info: {str(e)}")


# Initialize E2B client
e2b_client = E2BClient(E2B_API_KEY) if E2B_API_KEY else None


# Helper Functions
def parse_test_results(stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
    """
    Parse test results from command output
    Supports Jest, Mocha, pytest, Go test, etc.
    """
    test_results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "tests": []
    }
    
    # Jest/Mocha pattern: "Tests: 5 passed, 5 total"
    if "Tests:" in stdout:
        import re
        match = re.search(r'Tests:\s+(\d+)\s+passed.*?(\d+)\s+total', stdout)
        if match:
            test_results["passed"] = int(match.group(1))
            test_results["total"] = int(match.group(2))
            test_results["failed"] = test_results["total"] - test_results["passed"]
            return test_results
    
    # pytest pattern: "5 passed in 0.23s"
    if "passed" in stdout and "pytest" in stdout.lower():
        import re
        match = re.search(r'(\d+)\s+passed', stdout)
        if match:
            test_results["passed"] = int(match.group(1))
            test_results["total"] = test_results["passed"]
            return test_results
    
    # Go test pattern: "PASS" or "FAIL"
    if "PASS" in stdout or "FAIL" in stdout:
        lines = stdout.split('\n')
        for line in lines:
            if line.startswith('PASS'):
                test_results["passed"] += 1
            elif line.startswith('FAIL'):
                test_results["failed"] += 1
        test_results["total"] = test_results["passed"] + test_results["failed"]
        if test_results["total"] > 0:
            return test_results
    
    # If no pattern matched but exit code is 0, assume success
    if not stderr:
        return None
    
    return None


async def auto_cleanup_sandbox(sandbox_id: str, delay: int = 3600):
    """Auto-cleanup sandbox after delay"""
    await asyncio.sleep(delay)
    
    if sandbox_id in active_sandboxes:
        try:
            if e2b_client:
                await e2b_client.delete_sandbox(sandbox_id)
            del active_sandboxes[sandbox_id]
            print(f"Auto-cleaned up sandbox {sandbox_id}")
        except Exception as e:
            print(f"Error auto-cleaning sandbox {sandbox_id}: {e}")


# API Endpoints
@app.post("/sandbox/create", response_model=SandboxResponse)
async def create_sandbox(request: SandboxCreateRequest, background_tasks: BackgroundTasks):
    """
    Create a new sandbox VM
    """
    if not e2b_client:
        raise HTTPException(status_code=500, detail="E2B API key not configured")
    
    try:
        # Map environment to E2B template
        template_map = {
            "nodejs-18": "base",  # E2B base includes Node.js
            "python-3.11": "base",
            "go-1.21": "base"
        }
        template = template_map.get(request.environment, "base")
        
        # Create sandbox via E2B
        sandbox_data = await e2b_client.create_sandbox(template, request.timeout)
        sandbox_id = sandbox_data.get("sandboxId") or sandbox_data.get("id")
        
        # Track sandbox
        active_sandboxes[sandbox_id] = {
            "sandbox_id": sandbox_id,
            "environment": request.environment,
            "status": "ready",
            "created_at": datetime.utcnow().isoformat(),
            "executions": 0,
            "uptime_start": datetime.utcnow().timestamp()
        }
        
        # Schedule auto-cleanup
        background_tasks.add_task(auto_cleanup_sandbox, sandbox_id, request.timeout)
        
        return SandboxResponse(
            sandbox_id=sandbox_id,
            status="ready",
            connection={
                "url": f"{E2B_BASE_URL}/sandboxes/{sandbox_id}",
                "token": E2B_API_KEY
            },
            created_at=active_sandboxes[sandbox_id]["created_at"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sandbox/{sandbox_id}/execute", response_model=ExecuteResponse)
async def execute_code(sandbox_id: str, request: ExecuteRequest):
    """
    Execute code in sandbox
    """
    if not e2b_client:
        raise HTTPException(status_code=500, detail="E2B API key not configured")
    
    if sandbox_id not in active_sandboxes:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    
    try:
        execution_id = f"exec-{datetime.utcnow().timestamp()}"
        results = []
        
        # Write files to sandbox
        for filename, content in request.files.items():
            await e2b_client.write_file(sandbox_id, filename, content)
        
        # Execute commands sequentially
        for command in request.commands:
            start_time = datetime.utcnow().timestamp()
            
            # Execute command
            result = await e2b_client.execute_code(sandbox_id, command, "bash")
            
            end_time = datetime.utcnow().timestamp()
            duration = end_time - start_time
            
            # Extract results
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            exit_code = result.get("exitCode", 0)
            
            # Parse test results if this looks like a test command
            test_results = None
            if any(test_cmd in command for test_cmd in ["test", "pytest", "jest", "mocha", "go test"]):
                test_results = parse_test_results(stdout, stderr)
            
            results.append(CommandResult(
                command=command,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                test_results=test_results
            ))
            
            # Stop on first failure
            if exit_code != 0:
                break
        
        # Update sandbox stats
        active_sandboxes[sandbox_id]["executions"] += 1
        
        return ExecuteResponse(
            execution_id=execution_id,
            status="completed",
            results=results
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sandbox/{sandbox_id}/status", response_model=SandboxStatus)
async def get_sandbox_status(sandbox_id: str):
    """
    Get sandbox status
    """
    if sandbox_id not in active_sandboxes:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    
    sandbox = active_sandboxes[sandbox_id]
    uptime = int(datetime.utcnow().timestamp() - sandbox["uptime_start"])
    
    # Get resource usage from E2B (if available)
    resources = {
        "cpu_usage": 0,
        "memory_usage": 0,
        "disk_usage": 0
    }
    
    if e2b_client:
        try:
            info = await e2b_client.get_sandbox_info(sandbox_id)
            # E2B may provide resource info
            resources = info.get("resources", resources)
        except:
            pass
    
    return SandboxStatus(
        sandbox_id=sandbox_id,
        status=sandbox["status"],
        uptime=uptime,
        resources=resources,
        executions=sandbox["executions"]
    )


@app.delete("/sandbox/{sandbox_id}")
async def destroy_sandbox(sandbox_id: str):
    """
    Destroy sandbox
    """
    if sandbox_id not in active_sandboxes:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    
    try:
        if e2b_client:
            await e2b_client.delete_sandbox(sandbox_id)
        
        sandbox = active_sandboxes[sandbox_id]
        uptime = int(datetime.utcnow().timestamp() - sandbox["uptime_start"])
        executions = sandbox["executions"]
        
        del active_sandboxes[sandbox_id]
        
        return {
            "sandbox_id": sandbox_id,
            "status": "destroyed",
            "total_uptime": uptime,
            "total_executions": executions
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sandbox/{sandbox_id}/snapshot", response_model=SnapshotResponse)
async def create_snapshot(sandbox_id: str, request: SnapshotRequest):
    """
    Create sandbox snapshot (E2B Pro feature)
    """
    if sandbox_id not in active_sandboxes:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    
    # Note: Snapshot feature may require E2B Pro
    # This is a placeholder implementation
    snapshot_id = f"snap-{datetime.utcnow().timestamp()}"
    
    return SnapshotResponse(
        snapshot_id=snapshot_id,
        size=0,  # Would be populated by E2B
        created_at=datetime.utcnow().isoformat()
    )


@app.post("/sandbox/{sandbox_id}/restore")
async def restore_snapshot(sandbox_id: str, request: RestoreRequest):
    """
    Restore sandbox from snapshot (E2B Pro feature)
    """
    if sandbox_id not in active_sandboxes:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    
    # Note: Snapshot feature may require E2B Pro
    # This is a placeholder implementation
    
    return {
        "status": "restored",
        "snapshot_id": request.snapshot_id
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sandbox",
        "active_sandboxes": len(active_sandboxes),
        "e2b_configured": e2b_client is not None
    }


@app.get("/sandboxes")
async def list_sandboxes():
    """List all active sandboxes"""
    return {
        "sandboxes": [
            {
                "sandbox_id": sid,
                "status": info["status"],
                "environment": info["environment"],
                "uptime": int(datetime.utcnow().timestamp() - info["uptime_start"]),
                "executions": info["executions"]
            }
            for sid, info in active_sandboxes.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
