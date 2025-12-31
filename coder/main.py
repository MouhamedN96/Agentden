"""
Autonomous Coder Service - Feature Implementation
Based on autonomous-coding pattern with n8n webhook integration
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

app = FastAPI(title="Autonomous Coder Service", version="1.0.0")

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
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


class SessionResponse(BaseModel):
    session_id: str
    status: str
    project_dir: str


class ProgressWebhook(BaseModel):
    event: str = "test_progress"
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
    """
    Create feature_list.json from council plan
    Returns total number of features
    """
    features = plan.get("features", [])
    
    # Convert plan features to test format
    feature_list = []
    for feat in features:
        feature_list.append({
            "id": feat.get("id", f"feat-{len(feature_list)}"),
            "category": feat.get("category", "General"),
            "description": feat.get("description", ""),
            "test_cases": feat.get("test_cases", []),
            "priority": feat.get("priority", "medium"),
            "passes": False,
            "implemented_at": None
        })
    
    # Write to feature_list.json
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


def mark_feature_complete(project_dir: Path, feature_id: str) -> List[str]:
    """
    Mark a feature as complete and return its test descriptions
    """
    feature_file = project_dir / "feature_list.json"
    
    with open(feature_file, "r") as f:
        features = json.load(f)
    
    completed_tests = []
    for feat in features:
        if feat["id"] == feature_id:
            feat["passes"] = True
            feat["implemented_at"] = datetime.utcnow().isoformat()
            # Format test descriptions
            for test in feat.get("test_cases", []):
                completed_tests.append(f"[{feat['category']}] {test}")
            break
    
    with open(feature_file, "w") as f:
        json.dump(features, f, indent=2)
    
    return completed_tests


# Simulated autonomous coding (placeholder for actual Claude Agent SDK integration)
async def simulate_feature_implementation(
    session_id: str,
    project_dir: Path,
    plan: Dict,
    webhook_url: str,
    max_iterations: int
):
    """
    Simulate autonomous coding process
    In production, this would use Claude Agent SDK
    """
    try:
        active_sessions[session_id]["status"] = "running"
        
        # Create feature list
        total_features = create_feature_list(project_dir, plan)
        
        # Initialize git repo
        os.system(f"cd {project_dir} && git init")
        
        # Simulate implementing features one by one
        feature_file = project_dir / "feature_list.json"
        with open(feature_file, "r") as f:
            features = json.load(f)
        
        for i, feature in enumerate(features):
            if i >= max_iterations:
                break
            
            # Simulate implementation time
            await asyncio.sleep(2)  # In production, this is actual coding time
            
            # Mark feature complete
            completed_tests = mark_feature_complete(project_dir, feature["id"])
            
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
            active_sessions[session_id]["git_commits"] += 1
            
            # Simulate git commit
            os.system(f"cd {project_dir} && git add . && git commit -m 'Implement {feature['id']}'")
        
        # Mark session complete
        active_sessions[session_id]["status"] = "completed"
        
        # Final webhook
        passing, total = count_passing_tests(project_dir)
        final_payload = {
            "event": "implementation_complete",
            "session_id": session_id,
            "passing": passing,
            "total": total,
            "percentage": 100.0,
            "project": project_dir.name,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        await send_progress_webhook(webhook_url, final_payload)
        
    except Exception as e:
        active_sessions[session_id]["status"] = "failed"
        active_sessions[session_id]["error"] = str(e)
        print(f"Session {session_id} failed: {e}")


# API Endpoints
@app.post("/code/implement", response_model=SessionResponse)
async def implement_feature(request: ImplementRequest, background_tasks: BackgroundTasks):
    """
    Start autonomous coding session
    """
    try:
        # Create session ID
        session_id = f"session-{datetime.utcnow().timestamp()}"
        
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
            "webhook_url": request.webhook_url,
            "progress": {"passing": 0, "total": 0, "percentage": 0},
            "current_feature": "Initializing...",
            "git_commits": 0,
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Start implementation in background
        background_tasks.add_task(
            simulate_feature_implementation,
            session_id,
            project_dir,
            request.plan,
            request.webhook_url,
            request.max_iterations
        )
        
        return SessionResponse(
            session_id=session_id,
            status="started",
            project_dir=str(project_dir)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/code/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str):
    """
    Get status of coding session
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    return StatusResponse(
        session_id=session_id,
        status=session["status"],
        progress=session["progress"],
        current_feature=session["current_feature"],
        git_commits=session["git_commits"]
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "autonomous-coder",
        "active_sessions": len(active_sessions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
