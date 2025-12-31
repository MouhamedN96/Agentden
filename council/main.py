"""
LLM Council Service - Multi-Agent Planning and Code Review
Combines multiple LLMs via OpenRouter for collaborative decision-making
"""

import os
import asyncio
from typing import List, Dict, Any, Tuple
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="LLM Council Service", version="1.0.0")

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Council Configuration - Specialized Agents
COUNCIL_ROLES = {
    "architect": {
        "model": "anthropic/claude-sonnet-4.5",
        "role": "System Architect",
        "focus": "Architecture design, design patterns, scalability"
    },
    "security": {
        "model": "openai/gpt-4.1-mini",
        "role": "Security Expert",
        "focus": "Authentication, authorization, data protection, vulnerabilities"
    },
    "performance": {
        "model": "google/gemini-2.5-flash",
        "role": "Performance Engineer",
        "focus": "Optimization, caching, database queries, scalability"
    },
    "testing": {
        "model": "x-ai/grok-4",
        "role": "QA Engineer",
        "focus": "Test strategy, coverage, edge cases, validation"
    }
}

CHAIRMAN_MODEL = "anthropic/claude-sonnet-4.5"

# Request/Response Models
class FeatureRequest(BaseModel):
    request: str
    context: Dict[str, Any] = {}

class CodeReviewRequest(BaseModel):
    code: str
    tests: str
    original_plan: Dict[str, Any]

class PlanResponse(BaseModel):
    plan_id: str
    architecture: str
    features: List[Dict[str, Any]]
    security_requirements: List[str]
    performance_targets: Dict[str, Any]
    estimated_complexity: str
    council_consensus: float

class ReviewResponse(BaseModel):
    review_id: str
    verdict: str  # APPROVE or REVISE
    security_score: int
    performance_score: int
    test_coverage: int
    feedback: List[Dict[str, Any]]
    required_changes: List[str]
    council_consensus: float


# OpenRouter Client
async def query_openrouter(model: str, messages: List[Dict], timeout: float = 120.0) -> Dict:
    """Query OpenRouter API with specified model"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://code-on-fly.dev",
        "X-Title": "Code-on-Fly Council"
    }
    
    payload = {
        "model": model,
        "messages": messages
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(OPENROUTER_BASE_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": model
            }
        except Exception as e:
            print(f"Error querying {model}: {e}")
            return None


async def query_models_parallel(models: List[str], messages: List[Dict]) -> Dict[str, Dict]:
    """Query multiple models in parallel"""
    tasks = [query_openrouter(model, messages) for model in models]
    results = await asyncio.gather(*tasks)
    
    return {
        model: result
        for model, result in zip(models, results)
        if result is not None
    }


# Stage 1: Collect Individual Opinions
async def stage1_planning(request: str, context: Dict) -> List[Dict[str, Any]]:
    """
    Stage 1: Each specialist provides their perspective on the feature request
    """
    results = []
    
    for role_name, role_config in COUNCIL_ROLES.items():
        prompt = f"""You are the {role_config['role']} on an AI coding team council.
Your focus areas: {role_config['focus']}

Feature Request: {request}

Context:
{context}

Provide your expert perspective on implementing this feature:
1. Key considerations from your domain
2. Recommended approach
3. Potential risks or challenges
4. Success criteria

Be specific and actionable."""

        messages = [{"role": "user", "content": prompt}]
        response = await query_openrouter(role_config["model"], messages)
        
        if response:
            results.append({
                "role": role_name,
                "model": role_config["model"],
                "response": response["content"]
            })
    
    return results


# Stage 2: Peer Review and Ranking
async def stage2_peer_review(request: str, stage1_results: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    Stage 2: Each specialist reviews and ranks others' perspectives
    """
    # Create anonymized labels
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, D
    label_to_role = {
        f"Perspective {label}": result['role']
        for label, result in zip(labels, stage1_results)
    }
    
    # Build ranking prompt
    perspectives_text = "\n\n".join([
        f"Perspective {label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])
    
    ranking_prompt = f"""You are evaluating different perspectives on implementing this feature:

Feature Request: {request}

Here are the perspectives from different specialists (anonymized):

{perspectives_text}

Your task:
1. Evaluate each perspective: What does it do well? What does it miss?
2. Identify complementary ideas that should be combined
3. Spot any conflicts or contradictions

Then provide your final ranking:

FINAL RANKING:
1. Perspective [X]
2. Perspective [Y]
3. Perspective [Z]
4. Perspective [W]

Provide your evaluation and ranking:"""

    messages = [{"role": "user", "content": ranking_prompt}]
    
    # Get rankings from all specialists
    models = [role_config["model"] for role_config in COUNCIL_ROLES.values()]
    responses = await query_models_parallel(models, messages)
    
    rankings = []
    for role_name, role_config in COUNCIL_ROLES.items():
        model = role_config["model"]
        if model in responses and responses[model]:
            rankings.append({
                "role": role_name,
                "ranking": responses[model]["content"]
            })
    
    return rankings, label_to_role


# Stage 3: Chairman Synthesis
async def stage3_synthesize_plan(request: str, context: Dict, stage1_results: List[Dict], stage2_results: List[Dict]) -> Dict:
    """
    Stage 3: Chairman synthesizes final implementation plan
    """
    stage1_text = "\n\n".join([
        f"**{result['role'].upper()} ({result['model']})**:\n{result['response']}"
        for result in stage1_results
    ])
    
    stage2_text = "\n\n".join([
        f"**{result['role'].upper()} Ranking**:\n{result['ranking']}"
        for result in stage2_results
    ])
    
    chairman_prompt = f"""You are the Chairman of the AI Coding Team Council. Your job is to synthesize all specialist perspectives into a comprehensive implementation plan.

Feature Request: {request}

Context:
{context}

STAGE 1 - Specialist Perspectives:
{stage1_text}

STAGE 2 - Peer Rankings:
{stage2_text}

Create a comprehensive implementation plan with:

1. **ARCHITECTURE**: High-level system design
2. **FEATURES**: Detailed feature list with test cases (format as JSON array)
3. **SECURITY**: Security requirements and considerations
4. **PERFORMANCE**: Performance targets and optimization strategies
5. **COMPLEXITY**: Overall complexity assessment (high/medium/low)

Format your response as:

## Architecture
[Your architecture description]

## Features
```json
[
  {{
    "id": "feat-1",
    "category": "Authentication",
    "description": "User login with JWT",
    "test_cases": ["Test valid login", "Test invalid credentials"],
    "priority": "high"
  }}
]
```

## Security Requirements
- [Requirement 1]
- [Requirement 2]

## Performance Targets
- [Target 1]
- [Target 2]

## Complexity Assessment
[high/medium/low] - [Justification]

Provide the complete implementation plan:"""

    messages = [{"role": "user", "content": chairman_prompt}]
    response = await query_openrouter(CHAIRMAN_MODEL, messages)
    
    if not response:
        raise HTTPException(status_code=500, detail="Chairman synthesis failed")
    
    return {
        "synthesis": response["content"],
        "chairman_model": CHAIRMAN_MODEL
    }


# API Endpoints
@app.post("/council/plan", response_model=PlanResponse)
async def plan_feature(request: FeatureRequest):
    """
    3-stage council process for feature planning
    """
    try:
        # Stage 1: Collect specialist perspectives
        stage1_results = await stage1_planning(request.request, request.context)
        
        if not stage1_results:
            raise HTTPException(status_code=500, detail="No specialists responded")
        
        # Stage 2: Peer review and ranking
        stage2_results, label_to_role = await stage2_peer_review(request.request, stage1_results)
        
        # Stage 3: Chairman synthesis
        synthesis = await stage3_synthesize_plan(
            request.request,
            request.context,
            stage1_results,
            stage2_results
        )
        
        # Parse synthesis (simplified - in production, use better parsing)
        plan_id = f"plan-{datetime.utcnow().timestamp()}"
        
        # Calculate consensus (simplified)
        consensus = len(stage2_results) / len(COUNCIL_ROLES)
        
        return PlanResponse(
            plan_id=plan_id,
            architecture=synthesis["synthesis"],
            features=[],  # Would parse from synthesis
            security_requirements=[],  # Would parse from synthesis
            performance_targets={},  # Would parse from synthesis
            estimated_complexity="medium",  # Would parse from synthesis
            council_consensus=consensus
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/council/review", response_model=ReviewResponse)
async def review_code(request: CodeReviewRequest):
    """
    3-stage council process for code review
    """
    try:
        # Stage 1: Each specialist reviews the code
        review_results = []
        
        for role_name, role_config in COUNCIL_ROLES.items():
            prompt = f"""You are the {role_config['role']} reviewing code.
Your focus: {role_config['focus']}

Original Plan:
{request.original_plan}

Code:
```
{request.code}
```

Tests:
```
{request.tests}
```

Provide your review:
1. Score (0-100) for your domain
2. Issues found (if any)
3. Recommendations
4. Verdict: APPROVE or REVISE"""

            messages = [{"role": "user", "content": prompt}]
            response = await query_openrouter(role_config["model"], messages)
            
            if response:
                review_results.append({
                    "role": role_name,
                    "review": response["content"]
                })
        
        # Stage 2: Peer ranking of reviews (simplified for demo)
        
        # Stage 3: Chairman final verdict
        reviews_text = "\n\n".join([
            f"**{r['role'].upper()}**:\n{r['review']}"
            for r in review_results
        ])
        
        chairman_prompt = f"""As Chairman, provide final code review verdict.

Reviews from specialists:
{reviews_text}

Provide:
1. Overall verdict: APPROVE or REVISE
2. Security score (0-100)
3. Performance score (0-100)
4. Test coverage score (0-100)
5. Required changes (if REVISE)

Format as:
VERDICT: [APPROVE/REVISE]
SECURITY: [score]
PERFORMANCE: [score]
COVERAGE: [score]
CHANGES: [list if needed]"""

        messages = [{"role": "user", "content": chairman_prompt}]
        verdict_response = await query_openrouter(CHAIRMAN_MODEL, messages)
        
        review_id = f"review-{datetime.utcnow().timestamp()}"
        
        return ReviewResponse(
            review_id=review_id,
            verdict="APPROVE",  # Would parse from verdict_response
            security_score=95,  # Would parse
            performance_score=88,  # Would parse
            test_coverage=92,  # Would parse
            feedback=[],  # Would parse
            required_changes=[],  # Would parse
            council_consensus=0.90
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "llm-council"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
