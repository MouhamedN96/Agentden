"""
Enhanced Council Service with Multi-LLM Support
Supports Groq, OpenRouter, Ollama, Anthropic, OpenAI
"""

import os
import json
import re
import sys
from typing import Dict, Any, List
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bridge.lib.llm_providers import LLMRouter, LLMProvider, LLMClient

load_dotenv()

app = FastAPI(title="Enhanced Council Service with Multi-LLM", version="3.0.0")

# Initialize LLM Router
llm_router = LLMRouter()


# Request/Response Models
class CodeReviewRequest(BaseModel):
    code: str
    language: str = "javascript"
    context: str = ""
    quality_gates: List[str] = ["qa", "security", "performance"]
    llm_preference: str = "balanced"  # fast, cheap, quality, balanced


class SecurityScanRequest(BaseModel):
    code: str
    language: str = "javascript"
    llm_preference: str = "fast"


class PerformanceScanRequest(BaseModel):
    code: str
    language: str = "javascript"
    llm_preference: str = "fast"


class TestGenerationRequest(BaseModel):
    code: str
    language: str = "javascript"
    test_framework: str = "jest"
    llm_preference: str = "balanced"


class FixRequest(BaseModel):
    code: str
    language: str
    findings: List[Dict[str, Any]]
    llm_preference: str = "balanced"


# Agent Base Class
class Agent:
    """Base agent class with multi-LLM support"""
    
    def __init__(self, name: str):
        self.name = name
    
    async def call_llm(self, prompt: str, task_type: str = "balanced") -> str:
        """Call LLM with automatic provider selection"""
        try:
            client = llm_router.get_client(task_type)
            messages = [{"role": "user", "content": prompt}]
            response = await client.chat(messages)
            return response
        except Exception as e:
            print(f"LLM call error: {e}")
            raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            
            return json.loads(response)
        except json.JSONDecodeError:
            # Return default structure on parse error
            return self.get_default_response()
    
    def get_default_response(self) -> Dict[str, Any]:
        """Get default response structure"""
        return {
            "findings": [],
            "score": 50
        }


# QA Agent
class QAAgent(Agent):
    """Quality Assurance Agent"""
    
    def __init__(self):
        super().__init__("QA Agent")
    
    async def analyze(self, code: str, language: str, context: str, task_type: str = "balanced") -> Dict[str, Any]:
        """Analyze code for testing quality"""
        
        prompt = f"""You are a QA expert. Analyze this {language} code and provide:

1. Test coverage assessment
2. Missing test cases
3. Edge cases not covered
4. Error handling gaps
5. Test recommendations

Code:
```{language}
{code}
```

Context: {context}

Respond in JSON format:
{{
  "findings": [
    {{
      "severity": "high|medium|low",
      "type": "missing_tests|edge_case|error_handling",
      "description": "...",
      "location": "line X or function name",
      "fix": "..."
    }}
  ],
  "coverage": {{
    "estimated_lines": 0-100,
    "estimated_branches": 0-100,
    "estimated_functions": 0-100
  }},
  "score": 0-100
}}"""

        response = await self.call_llm(prompt, task_type)
        result = self.parse_json_response(response)
        
        return {
            "name": self.name,
            "status": "completed",
            "findings": result.get("findings", []),
            "coverage": result.get("coverage", {}),
            "score": result.get("score", 50)
        }
    
    async def generate_tests(self, code: str, language: str, test_framework: str, task_type: str = "balanced") -> Dict[str, Any]:
        """Generate test cases for code"""
        
        prompt = f"""Generate comprehensive test cases for this {language} code using {test_framework}.

Code:
```{language}
{code}
```

Generate tests that cover:
1. Normal cases
2. Edge cases
3. Error cases
4. Boundary conditions

Respond in JSON format:
{{
  "test_code": "...",
  "test_count": 5,
  "test_cases": [
    {{
      "name": "test name",
      "type": "unit|integration|edge",
      "description": "..."
    }}
  ],
  "coverage": {{
    "functions": 100,
    "lines": 90,
    "branches": 85
  }}
}}"""

        response = await self.call_llm(prompt, task_type)
        result = self.parse_json_response(response)
        
        # Fallback if JSON parsing failed
        if not result.get("test_code"):
            code_match = re.search(r'```(?:\w+)?\s*(.*?)\s*```', response, re.DOTALL)
            test_code = code_match.group(1) if code_match else response
            result["test_code"] = test_code
        
        return result


# Security Agent
class SecurityAgent(Agent):
    """Security Agent - Uses fastest LLM for quick scans"""
    
    def __init__(self):
        super().__init__("Security Agent")
    
    async def analyze(self, code: str, language: str, context: str, task_type: str = "fast") -> Dict[str, Any]:
        """Analyze code for security vulnerabilities"""
        
        prompt = f"""You are a security expert and penetration tester. Analyze this {language} code for vulnerabilities:

1. OWASP Top 10 vulnerabilities
2. SQL injection risks
3. XSS vulnerabilities
4. Authentication/authorization issues
5. Prompt injection (for AI features)
6. Secret exposure
7. Input validation issues

Code:
```{language}
{code}
```

Context: {context}

For each vulnerability found, provide:
- Severity (critical/high/medium/low)
- Type of vulnerability
- Description
- Location in code
- Example exploit
- Fix recommendation

Respond in JSON format:
{{
  "findings": [
    {{
      "severity": "critical|high|medium|low",
      "type": "sql_injection|xss|auth_bypass|prompt_injection|secret_exposure|...",
      "description": "...",
      "location": "line X",
      "exploit": "example attack",
      "fix": "..."
    }}
  ],
  "score": 0-100
}}"""

        response = await self.call_llm(prompt, task_type)
        result = self.parse_json_response(response)
        
        return {
            "name": self.name,
            "status": "completed",
            "findings": result.get("findings", []),
            "score": result.get("score", 50)
        }


# Performance Agent
class PerformanceAgent(Agent):
    """Performance Agent"""
    
    def __init__(self):
        super().__init__("Performance Agent")
    
    async def analyze(self, code: str, language: str, context: str, task_type: str = "fast") -> Dict[str, Any]:
        """Analyze code for performance issues"""
        
        prompt = f"""You are a performance optimization expert. Analyze this {language} code for:

1. N+1 query problems
2. Inefficient algorithms (O(n²) or worse)
3. Memory leaks
4. Unnecessary computations
5. Blocking operations
6. Missing caching opportunities

Code:
```{language}
{code}
```

Context: {context}

Respond in JSON format:
{{
  "findings": [
    {{
      "severity": "high|medium|low",
      "type": "n_plus_one|inefficient_algorithm|memory_leak|blocking_operation|...",
      "description": "...",
      "location": "line X",
      "impact": "performance impact description",
      "fix": "..."
    }}
  ],
  "benchmarks": {{
    "estimated_complexity": "O(n)",
    "estimated_memory": "high|medium|low"
  }},
  "score": 0-100
}}"""

        response = await self.call_llm(prompt, task_type)
        result = self.parse_json_response(response)
        
        return {
            "name": self.name,
            "status": "completed",
            "findings": result.get("findings", []),
            "benchmarks": result.get("benchmarks", {}),
            "score": result.get("score", 50)
        }


# Architecture Agent
class ArchitectureAgent(Agent):
    """Architecture Agent"""
    
    def __init__(self):
        super().__init__("Architecture Agent")
    
    async def analyze(self, code: str, language: str, context: str, task_type: str = "balanced") -> Dict[str, Any]:
        """Analyze code architecture and design"""
        
        prompt = f"""You are a software architecture expert. Analyze this {language} code for:

1. Design pattern usage
2. SOLID principles adherence
3. Code structure and organization
4. Coupling and cohesion
5. Maintainability issues
6. Code smells

Code:
```{language}
{code}
```

Context: {context}

Respond in JSON format:
{{
  "findings": [
    {{
      "severity": "high|medium|low",
      "type": "tight_coupling|low_cohesion|code_smell|...",
      "description": "...",
      "location": "...",
      "fix": "..."
    }}
  ],
  "metrics": {{
    "maintainability_index": 0-100,
    "coupling": "high|medium|low",
    "cohesion": "high|medium|low"
  }},
  "score": 0-100
}}"""

        response = await self.call_llm(prompt, task_type)
        result = self.parse_json_response(response)
        
        return {
            "name": self.name,
            "status": "completed",
            "findings": result.get("findings", []),
            "metrics": result.get("metrics", {}),
            "score": result.get("score", 50)
        }


# Chairman Agent
class ChairmanAgent:
    """Chairman Agent - Synthesizes findings from all agents"""
    
    def synthesize(self, agents_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize findings from all agents"""
        
        all_findings = []
        for agent in agents_results:
            for finding in agent.get("findings", []):
                all_findings.append({
                    **finding,
                    "agent": agent["name"]
                })
        
        # Count by severity
        summary = {
            "critical": sum(1 for f in all_findings if f.get("severity") == "critical"),
            "high": sum(1 for f in all_findings if f.get("severity") == "high"),
            "medium": sum(1 for f in all_findings if f.get("severity") == "medium"),
            "low": sum(1 for f in all_findings if f.get("severity") == "low")
        }
        
        # Calculate overall score (weighted average)
        scores = [agent.get("score", 50) for agent in agents_results]
        overall_score = sum(scores) // len(scores) if scores else 50
        
        # Determine quality gate
        quality_gate = "passed" if summary["critical"] == 0 and summary["high"] == 0 and overall_score >= 70 else "failed"
        
        # Priority fixes (critical and high severity)
        priority_fixes = [
            {
                "priority": i + 1,
                "issue": f["description"],
                "severity": f["severity"],
                "agent": f["agent"],
                "fix": f.get("fix", "Manual review required")
            }
            for i, f in enumerate(sorted(
                [f for f in all_findings if f.get("severity") in ["critical", "high"]],
                key=lambda x: 0 if x.get("severity") == "critical" else 1
            )[:10])
        ]
        
        # Generate recommendation
        if quality_gate == "passed":
            recommendation = "Code meets quality standards and is ready for production."
        elif summary["critical"] > 0:
            recommendation = f"CRITICAL: {summary['critical']} critical issue(s) must be fixed before deployment."
        elif summary["high"] > 0:
            recommendation = f"Fix {summary['high']} high-priority issue(s) before deployment."
        else:
            recommendation = "Address medium and low priority issues to improve code quality."
        
        return {
            "overall_score": overall_score,
            "quality_gate": quality_gate,
            "summary": summary,
            "priority_fixes": priority_fixes,
            "agents": agents_results,
            "recommendation": recommendation
        }


# Initialize agents
qa_agent = QAAgent()
security_agent = SecurityAgent()
performance_agent = PerformanceAgent()
architecture_agent = ArchitectureAgent()
chairman_agent = ChairmanAgent()


# API Endpoints

@app.post("/council/review")
async def review_code(request: CodeReviewRequest):
    """Comprehensive code review by all agents"""
    
    agents_results = []
    task_type = request.llm_preference
    
    # Run requested agents
    if "qa" in request.quality_gates:
        qa_result = await qa_agent.analyze(request.code, request.language, request.context, task_type)
        agents_results.append(qa_result)
    
    if "security" in request.quality_gates:
        security_result = await security_agent.analyze(request.code, request.language, request.context, "fast")
        agents_results.append(security_result)
    
    if "performance" in request.quality_gates:
        performance_result = await performance_agent.analyze(request.code, request.language, request.context, "fast")
        agents_results.append(performance_result)
    
    if "architecture" in request.quality_gates:
        architecture_result = await architecture_agent.analyze(request.code, request.language, request.context, task_type)
        agents_results.append(architecture_result)
    
    # Chairman synthesizes
    report = chairman_agent.synthesize(agents_results)
    
    return {
        "agents": agents_results,
        "report": report
    }


@app.post("/council/security")
async def security_scan(request: SecurityScanRequest):
    """Quick security scan"""
    result = await security_agent.analyze(request.code, request.language, "", request.llm_preference)
    return result


@app.post("/council/performance")
async def performance_scan(request: PerformanceScanRequest):
    """Quick performance scan"""
    result = await performance_agent.analyze(request.code, request.language, "", request.llm_preference)
    return result


@app.post("/council/qa/generate-tests")
async def generate_tests(request: TestGenerationRequest):
    """Generate test cases"""
    result = await qa_agent.generate_tests(request.code, request.language, request.test_framework, request.llm_preference)
    return result


@app.post("/council/fix")
async def apply_fixes(request: FixRequest):
    """Apply fixes to code based on findings"""
    
    agent = Agent("Fixer")
    
    findings_text = "\n".join([
        f"- {f['description']} (Fix: {f.get('fix', 'N/A')})"
        for f in request.findings
    ])
    
    prompt = f"""Fix the following issues in this {request.language} code:

{findings_text}

Original code:
```{request.language}
{request.code}
```

Provide the fixed code and explain what changes were made.

Respond in JSON format:
{{
  "fixed_code": "...",
  "changes": [
    {{
      "description": "...",
      "file": "main file",
      "lines": "X-Y"
    }}
  ],
  "fixes_applied": 3,
  "needs_review": false
}}"""

    response = await agent.call_llm(prompt, request.llm_preference)
    result = agent.parse_json_response(response)
    
    # Fallback if JSON parsing failed
    if not result.get("fixed_code"):
        code_match = re.search(r'```(?:\w+)?\s*(.*?)\s*```', response, re.DOTALL)
        fixed_code = code_match.group(1) if code_match else request.code
        result = {
            "fixed_code": fixed_code,
            "changes": [{"description": "Applied fixes", "file": "main", "lines": "N/A"}],
            "fixes_applied": len(request.findings),
            "needs_review": True
        }
    
    return result


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    available_providers = list(llm_router.providers.keys())
    return {
        "status": "healthy",
        "service": "enhanced-council-multi-llm",
        "llm_providers": available_providers,
        "provider_count": len(available_providers)
    }


@app.get("/providers")
async def list_providers():
    """List available LLM providers"""
    return {
        "available": list(llm_router.providers.keys()),
        "count": len(llm_router.providers)
    }


if __name__ == "__main__":
    import uvicorn
    
    # Print available providers
    print("\n" + "="*60)
    print("Enhanced Council Service - Multi-LLM Support")
    print("="*60)
    print(f"\nAvailable LLM Providers: {list(llm_router.providers.keys())}")
    print("\nStarting server on port 8001...")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
