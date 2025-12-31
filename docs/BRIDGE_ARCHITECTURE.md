# Bridge Architecture: Claude Code ↔ Council Agents

## Vision

**Transform your coding workflow** by bridging Claude Code's velocity with Council agents' scrutiny and quality benchmarking.

```
Claude Code (Fast) → Bridge → Council Agents (Quality) → Production-Ready Code
```

## Core Concept

### The Problem

**Claude Code alone**:
- ✅ Fast code generation
- ✅ Great for prototyping
- ❌ No automated testing
- ❌ No security review
- ❌ No performance analysis
- ❌ No quality gates

**Manual review**:
- ❌ Slow and tedious
- ❌ Easy to miss issues
- ❌ Inconsistent standards
- ❌ Blocks velocity

### The Solution: Bridge System

**Automated quality pipeline**:
```
Claude writes code
    ↓
Bridge captures code
    ↓
Council reviews in parallel:
  - QA Agent: Tests coverage, edge cases
  - Security Agent: Pen-testing, vulnerabilities
  - Performance Agent: Benchmarks, optimization
  - Architecture Agent: Design patterns, best practices
    ↓
Sandbox executes tests
    ↓
Report back to Claude
    ↓
Claude fixes issues
    ↓
Repeat until quality gates pass
    ↓
Production-ready code ✅
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Coding Assistants                     │
│  Claude Code | Manus | Gemini Code | Qwen Coder | GLM Code  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      Bridge Service                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │   MCP   │  │   API   │  │   ACP   │  │   A2A   │       │
│  │ Server  │  │  REST   │  │Protocol │  │  Link   │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       └────────────┴────────────┴─────────────┘            │
│                         │                                    │
│              ┌──────────┴──────────┐                        │
│              │   Request Router    │                        │
│              │  - Code submission  │                        │
│              │  - Session mgmt     │                        │
│              │  - Result streaming │                        │
│              └──────────┬──────────┘                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Council Service                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  QA Agent    │  │Security Agent│  │  Perf Agent  │     │
│  │- Test gen    │  │- Pen-testing │  │- Benchmarks  │     │
│  │- Coverage    │  │- OWASP scan  │  │- Profiling   │     │
│  │- Edge cases  │  │- Injection   │  │- Optimization│     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         └──────────────────┴──────────────────┘             │
│                         │                                    │
│              ┌──────────┴──────────┐                        │
│              │   Chairman Agent    │                        │
│              │  - Synthesize       │                        │
│              │  - Prioritize       │                        │
│              │  - Report           │                        │
│              └──────────┬──────────┘                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Sandbox Service                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Test VM     │  │  Security VM │  │   Perf VM    │     │
│  │- Run tests   │  │- Attack sims │  │- Load tests  │     │
│  │- Coverage    │  │- Vuln scan   │  │- Profiling   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Integration Protocols

### 1. MCP (Model Context Protocol)

**Purpose**: Native integration with Claude Desktop/Code

**How it works**:
```json
// Claude's MCP config
{
  "mcpServers": {
    "code-quality-bridge": {
      "command": "node",
      "args": ["/path/to/bridge-mcp-server.js"],
      "env": {
        "BRIDGE_URL": "http://localhost:8004"
      }
    }
  }
}
```

**Tools exposed to Claude**:
- `submit_code_for_review` - Send code to council
- `get_review_status` - Check review progress
- `get_review_report` - Get detailed feedback
- `apply_fixes` - Auto-apply suggested fixes

**Example usage in Claude**:
```
User: "Review this authentication code"

Claude: *uses submit_code_for_review tool*
→ Bridge receives code
→ Council reviews in parallel
→ Sandbox tests security
→ Report generated

Claude: *uses get_review_report tool*
← Receives: "3 critical issues found"
← Security: SQL injection vulnerability
← QA: Missing input validation tests
← Performance: N+1 query detected

Claude: *fixes issues and resubmits*
```

### 2. REST API

**Purpose**: Universal access for any client

**Endpoints**:

```
POST /api/v1/review/submit
- Submit code for review
- Returns: session_id

GET /api/v1/review/{session_id}/status
- Check review progress
- Returns: status, progress %

GET /api/v1/review/{session_id}/report
- Get detailed report
- Returns: findings by agent

POST /api/v1/review/{session_id}/fix
- Apply suggested fixes
- Returns: fixed code

WebSocket /api/v1/review/{session_id}/stream
- Real-time progress updates
- Streams: agent findings as they happen
```

**Example usage**:
```bash
# Submit code
curl -X POST http://localhost:8004/api/v1/review/submit \
  -H "Content-Type: application/json" \
  -d '{
    "code": "...",
    "language": "javascript",
    "context": "Express API authentication"
  }'
# → {"session_id": "rev-abc123"}

# Stream progress
wscat -c ws://localhost:8004/api/v1/review/rev-abc123/stream
# → {"agent": "qa", "status": "analyzing"}
# → {"agent": "security", "finding": "SQL injection risk"}
# → {"agent": "performance", "finding": "N+1 query"}
# → {"status": "complete", "score": 65/100}

# Get report
curl http://localhost:8004/api/v1/review/rev-abc123/report
```

### 3. ACP (Agent Communication Protocol)

**Purpose**: Agent-to-agent communication

**How it works**:
```
Agent A (Claude) → ACP Message → Bridge → Council Agents
                                            ↓
Agent A ← ACP Response ← Bridge ← Council Report
```

**Message format**:
```json
{
  "protocol": "acp/1.0",
  "from": "claude-code-assistant",
  "to": "council-qa-agent",
  "type": "code_review_request",
  "payload": {
    "code": "...",
    "language": "python",
    "context": "ML model training"
  },
  "reply_to": "claude-session-xyz"
}
```

**Response format**:
```json
{
  "protocol": "acp/1.0",
  "from": "council-qa-agent",
  "to": "claude-code-assistant",
  "type": "code_review_response",
  "in_reply_to": "claude-session-xyz",
  "payload": {
    "findings": [...],
    "score": 85,
    "recommendations": [...]
  }
}
```

### 4. A2A Link (Agent-to-Agent Link)

**Purpose**: Direct agent collaboration

**How it works**:
```
Claude Agent ←→ A2A Link ←→ Council Agents
     ↓                           ↓
  Writes code              Reviews code
     ↓                           ↓
  Receives feedback        Sends findings
     ↓                           ↓
  Applies fixes            Re-reviews
     ↓                           ↓
  Iterates until quality gates pass
```

**Features**:
- Bidirectional communication
- Real-time collaboration
- Shared context
- Iterative improvement

## Council Agents Specialization

### 1. QA Agent

**Role**: Test coverage and edge case detection

**Responsibilities**:
- Generate comprehensive test cases
- Identify edge cases
- Check test coverage
- Validate error handling
- Review assertions

**Output**:
```json
{
  "agent": "qa",
  "findings": [
    {
      "severity": "high",
      "type": "missing_tests",
      "description": "No tests for authentication failure",
      "suggestion": "Add test for invalid credentials"
    },
    {
      "severity": "medium",
      "type": "edge_case",
      "description": "Empty string input not tested",
      "suggestion": "Add test for empty username"
    }
  ],
  "coverage": {
    "lines": 65,
    "branches": 45,
    "functions": 80
  },
  "score": 70
}
```

### 2. Security Agent (Pen-Testing)

**Role**: Security vulnerability detection

**Responsibilities**:
- OWASP Top 10 scanning
- SQL injection testing
- XSS vulnerability detection
- Authentication bypass attempts
- Prompt injection testing (for AI features)
- Secret exposure detection

**Output**:
```json
{
  "agent": "security",
  "findings": [
    {
      "severity": "critical",
      "type": "sql_injection",
      "location": "line 45",
      "description": "Unsanitized user input in SQL query",
      "exploit": "' OR '1'='1",
      "fix": "Use parameterized queries"
    },
    {
      "severity": "high",
      "type": "prompt_injection",
      "location": "line 120",
      "description": "AI prompt accepts unvalidated user input",
      "exploit": "Ignore previous instructions and...",
      "fix": "Sanitize and validate AI inputs"
    }
  ],
  "score": 45
}
```

### 3. Performance Agent

**Role**: Performance optimization

**Responsibilities**:
- Benchmark execution time
- Memory profiling
- Database query optimization
- API response time analysis
- Load testing

**Output**:
```json
{
  "agent": "performance",
  "findings": [
    {
      "severity": "high",
      "type": "n_plus_one",
      "location": "line 78",
      "description": "N+1 query in user loop",
      "impact": "10x slower for 100 users",
      "fix": "Use eager loading"
    }
  ],
  "benchmarks": {
    "avg_response_time": "450ms",
    "p95_response_time": "1200ms",
    "memory_usage": "125MB",
    "queries_per_request": 15
  },
  "score": 60
}
```

### 4. Architecture Agent

**Role**: Design patterns and best practices

**Responsibilities**:
- Code structure review
- Design pattern validation
- SOLID principles check
- Dependency management
- Code maintainability

**Output**:
```json
{
  "agent": "architecture",
  "findings": [
    {
      "severity": "medium",
      "type": "tight_coupling",
      "location": "UserService",
      "description": "Direct database access in service layer",
      "fix": "Introduce repository pattern"
    }
  ],
  "metrics": {
    "cyclomatic_complexity": 12,
    "maintainability_index": 65,
    "coupling": "high",
    "cohesion": "medium"
  },
  "score": 75
}
```

### 5. Chairman Agent

**Role**: Synthesize and prioritize findings

**Responsibilities**:
- Aggregate all agent findings
- Prioritize issues by severity
- Generate actionable report
- Calculate overall quality score
- Provide fix recommendations

**Output**:
```json
{
  "agent": "chairman",
  "overall_score": 65,
  "quality_gate": "failed",
  "summary": {
    "critical": 1,
    "high": 3,
    "medium": 5,
    "low": 2
  },
  "priority_fixes": [
    {
      "priority": 1,
      "issue": "SQL injection vulnerability",
      "agent": "security",
      "fix": "Use parameterized queries"
    },
    {
      "priority": 2,
      "issue": "Missing authentication tests",
      "agent": "qa",
      "fix": "Add test cases for auth failures"
    }
  ],
  "recommendation": "Fix critical security issue before deployment"
}
```

## Workflow Examples

### Example 1: Claude Code → Bridge → Council

**Step 1: Claude writes code**
```javascript
// User to Claude: "Build a login endpoint"
app.post('/login', (req, res) => {
  const { username, password } = req.body;
  const user = db.query(`SELECT * FROM users WHERE username='${username}'`);
  if (user && user.password === password) {
    res.json({ token: generateToken(user) });
  }
});
```

**Step 2: User triggers review**
```
User: "Review this code with the council"
Claude: *uses submit_code_for_review MCP tool*
```

**Step 3: Bridge routes to council**
```
Bridge → QA Agent: Analyze tests
Bridge → Security Agent: Check vulnerabilities
Bridge → Performance Agent: Benchmark
```

**Step 4: Agents review in parallel**

**QA Agent**:
- ❌ No tests for invalid credentials
- ❌ No tests for SQL injection
- ❌ No tests for missing fields

**Security Agent**:
- 🚨 CRITICAL: SQL injection vulnerability
- 🚨 HIGH: Plain text password comparison
- ⚠️  MEDIUM: No rate limiting

**Performance Agent**:
- ⚠️  MEDIUM: Synchronous database query
- ℹ️  LOW: No caching

**Step 5: Chairman synthesizes**
```json
{
  "overall_score": 25/100,
  "quality_gate": "FAILED",
  "critical_issues": 2,
  "must_fix": [
    "SQL injection: Use parameterized queries",
    "Password security: Hash passwords with bcrypt"
  ]
}
```

**Step 6: Report back to Claude**
```
Bridge → Claude: Review complete
Claude receives:
  - 2 critical security issues
  - 3 missing test cases
  - Detailed fix recommendations
```

**Step 7: Claude fixes issues**
```javascript
// Claude rewrites with fixes
app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  
  // Input validation
  if (!username || !password) {
    return res.status(400).json({ error: 'Missing credentials' });
  }
  
  // Parameterized query (SQL injection fix)
  const user = await db.query(
    'SELECT * FROM users WHERE username = $1',
    [username]
  );
  
  if (!user) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  
  // Hash comparison (password security fix)
  const valid = await bcrypt.compare(password, user.password_hash);
  
  if (valid) {
    res.json({ token: generateToken(user) });
  } else {
    res.status(401).json({ error: 'Invalid credentials' });
  }
});
```

**Step 8: Re-review**
```
Claude: *resubmits for review*
Council: ✅ All critical issues resolved
         ✅ Security score: 95/100
         ✅ Quality gate: PASSED
```

### Example 2: Multi-Agent Collaboration

**Scenario**: Building a payment processing feature

**Claude writes initial code** → **Council reviews**

**QA Agent finds**: Missing refund test cases
**Security Agent finds**: PCI compliance issues
**Performance Agent finds**: Synchronous payment processing

**Chairman prioritizes**:
1. Fix PCI compliance (critical)
2. Add async payment processing (high)
3. Add refund tests (medium)

**Claude fixes issues** → **Re-review**

**Security Agent**: ✅ PCI compliant
**Performance Agent**: ✅ Async processing
**QA Agent**: ⚠️  Still missing edge case tests

**Claude adds edge case tests** → **Final review**

**All agents**: ✅ Production ready
**Overall score**: 92/100

## Quality Gates

### Gate 1: Security
- No critical vulnerabilities
- No high-severity issues
- Security score ≥ 80

### Gate 2: Testing
- Test coverage ≥ 70%
- All critical paths tested
- Edge cases covered

### Gate 3: Performance
- Response time < 500ms (p95)
- Memory usage reasonable
- No N+1 queries

### Gate 4: Architecture
- SOLID principles followed
- Low coupling
- High cohesion

**All gates must pass for production deployment**

## Multi-LLM Support

### Supported Assistants

1. **Claude Code** (via MCP)
2. **Manus** (via API)
3. **Gemini Code** (via API)
4. **Qwen Coder** (via API)
5. **GLM Code** (via API)

### Universal Bridge

**Any LLM can**:
- Submit code for review
- Receive standardized feedback
- Apply fixes
- Re-submit for validation

**Bridge handles**:
- Protocol translation
- Session management
- Result formatting
- Streaming updates

## Benefits

### For You

✅ **Velocity + Quality**: Fast coding with automated scrutiny
✅ **Catch issues early**: Before they reach production
✅ **Learn from feedback**: Improve coding patterns
✅ **Multi-LLM**: Use best tool for each task
✅ **Automated testing**: No manual review needed

### For Your Business

✅ **Higher quality**: Fewer bugs in production
✅ **Security**: Automated vulnerability detection
✅ **Performance**: Optimized from the start
✅ **Compliance**: Automated security checks
✅ **Scalability**: Quality gates enforce standards

## Technical Stack

### Bridge Service
- **Language**: Node.js/TypeScript
- **Framework**: Express.js
- **Protocols**: MCP, REST, WebSocket, ACP
- **Port**: 8004

### MCP Server
- **Language**: Node.js
- **SDK**: @modelcontextprotocol/sdk
- **Integration**: Claude Desktop config

### Council Service (Enhanced)
- **Language**: Python
- **Framework**: FastAPI
- **Agents**: QA, Security, Performance, Architecture, Chairman
- **Port**: 8001

### Sandbox Service (Enhanced)
- **Language**: Python
- **Framework**: FastAPI
- **VMs**: E2B sandboxes
- **Specialization**: Test, Security, Performance VMs
- **Port**: 8003

## Next Steps

1. **Implement Bridge Service** with all protocols
2. **Create MCP Server** for Claude integration
3. **Enhance Council Agents** with specializations
4. **Build specialized Sandbox VMs** for different tests
5. **Create integration examples** for each LLM
6. **Write comprehensive docs** and guides

## Cost Estimate

**Per code review**:
- Council analysis: $0.05-0.10
- Sandbox testing: $0.02-0.05
- **Total: $0.07-0.15**

**Monthly (200 reviews)**:
- Council: $10-20
- Sandbox: $4-10
- **Total: $14-30/month**

**Extremely affordable for the value!**

## Success Metrics

Track:
- **Quality score trend**: Improving over time?
- **Issues caught**: Before production
- **Fix time**: How fast issues resolved?
- **Gate pass rate**: First-time quality
- **Developer satisfaction**: Helpful feedback?

## Conclusion

This bridge transforms your coding workflow from **"code fast, debug later"** to **"code fast, ship quality"**.

**Claude's velocity + Council's scrutiny = Production-ready code at speed**
