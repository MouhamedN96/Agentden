# Sandbox VM Integration Architecture

## Overview

This document outlines the integration of sandbox VMs into Code-on-Fly, enabling autonomous agents to safely execute and test code in isolated environments.

## Why Sandbox VMs?

### Security Benefits
- **Isolation**: Code runs in completely isolated environments
- **Resource Limits**: CPU, memory, disk, and network constraints
- **No Host Contamination**: Failed or malicious code can't affect the host
- **Clean State**: Each session starts with a fresh environment

### Testing Benefits
- **Real Execution**: Test code in actual runtime environments
- **Multi-Language**: Support Node.js, Python, Go, Rust, etc.
- **Dependency Installation**: Install packages and test full stack
- **Integration Testing**: Test APIs, databases, external services

### Development Benefits
- **Parallel Execution**: Multiple sandboxes for concurrent projects
- **Snapshot/Restore**: Save working states, rollback on failure
- **Debugging**: Inspect running code, view logs, attach debuggers
- **Reproducibility**: Consistent environments across all sessions

## Architecture Options

### Option 1: E2B (Recommended for Quick Start)

**What is E2B?**
- Cloud-based code execution sandboxes
- Pre-built environments (Node.js, Python, etc.)
- API-first design
- Built for AI agents

**Pros:**
- ✅ Fastest to implement (API-based)
- ✅ No infrastructure management
- ✅ Built-in security and isolation
- ✅ File system access
- ✅ Process management
- ✅ Snapshot support

**Cons:**
- ❌ Costs per minute of usage
- ❌ Vendor lock-in
- ❌ Limited customization

**Cost:** ~$0.10-0.30 per hour per sandbox

### Option 2: Firecracker (Recommended for Production)

**What is Firecracker?**
- Lightweight microVM technology (AWS Lambda uses this)
- Boots in <125ms
- Minimal memory overhead (~5MB)
- Strong isolation via KVM

**Pros:**
- ✅ Self-hosted (no vendor lock-in)
- ✅ Very fast boot times
- ✅ Low resource overhead
- ✅ Production-grade security
- ✅ Full control

**Cons:**
- ❌ More complex setup
- ❌ Requires Linux host with KVM
- ❌ Need to manage infrastructure

**Cost:** Only infrastructure costs

### Option 3: Docker with Security Hardening

**What is it?**
- Docker containers with security constraints
- AppArmor/SELinux profiles
- Resource limits via cgroups
- Network isolation

**Pros:**
- ✅ Easy to implement
- ✅ Good ecosystem
- ✅ Familiar technology
- ✅ Fast startup

**Cons:**
- ❌ Weaker isolation than VMs
- ❌ Shared kernel vulnerabilities
- ❌ Container escape risks

**Cost:** Only infrastructure costs

### Option 4: Kata Containers

**What is it?**
- Combines container UX with VM security
- Each container runs in its own lightweight VM
- OCI-compatible

**Pros:**
- ✅ VM-level isolation
- ✅ Container-like UX
- ✅ Good balance of security and ease

**Cons:**
- ❌ More resource overhead than Docker
- ❌ Complex setup
- ❌ Requires nested virtualization

**Cost:** Only infrastructure costs

## Recommended Approach: Hybrid

**Phase 1 (MVP)**: E2B for quick validation
- Get sandbox integration working fast
- Test with real projects
- Validate the concept

**Phase 2 (Production)**: Migrate to Firecracker
- Self-hosted for cost optimization
- Full control over environment
- Scale as needed

## Integration Design

### Architecture Diagram

```
┌─────────────┐
│   Slack     │ User requests feature
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│  n8n Orchestrator    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  LLM Council         │ Plans implementation
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Autonomous Coder    │ Generates code
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Sandbox Service     │ ← NEW COMPONENT
│  - VM Orchestration  │
│  - Code Execution    │
│  - Test Running      │
│  - Result Collection │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Sandbox VMs         │
│  (E2B / Firecracker) │
└──────────────────────┘
```

### Component Responsibilities

**Sandbox Service (Port 8003)**
- Create/destroy sandbox VMs
- Execute code in sandboxes
- Run tests and collect results
- Manage sandbox lifecycle
- Handle timeouts and errors

**Autonomous Coder (Updated)**
- Generate code based on plan
- Send code to Sandbox Service
- Receive test results
- Iterate based on failures
- Mark features complete when tests pass

**n8n Workflow (Updated)**
- Add sandbox provisioning step
- Handle sandbox errors
- Monitor sandbox usage
- Clean up sandboxes after completion

## Data Flow

### 1. Sandbox Provisioning

```
Autonomous Coder → Sandbox Service: "Create sandbox for Node.js"
Sandbox Service → E2B/Firecracker: Provision VM
Sandbox Service → Autonomous Coder: {sandbox_id, connection_info}
```

### 2. Code Execution

```
Autonomous Coder → Sandbox Service: {
  sandbox_id: "sb-123",
  code: "const express = require('express')...",
  files: {
    "package.json": {...},
    "server.js": {...}
  },
  command: "npm install && npm test"
}

Sandbox Service → Sandbox VM: Write files, execute command
Sandbox VM → Sandbox Service: {
  stdout: "...",
  stderr: "...",
  exit_code: 0,
  test_results: {...}
}

Sandbox Service → Autonomous Coder: Test results
```

### 3. Iterative Testing

```
Loop until all tests pass:
  1. Autonomous Coder generates code
  2. Sandbox Service executes tests
  3. If tests fail:
     - Autonomous Coder analyzes errors
     - Generates fix
     - Repeat
  4. If tests pass:
     - Mark feature complete
     - Move to next feature
```

### 4. Cleanup

```
Autonomous Coder → Sandbox Service: "Destroy sandbox sb-123"
Sandbox Service → E2B/Firecracker: Terminate VM
Sandbox Service → Autonomous Coder: {status: "destroyed"}
```

## API Design

### Sandbox Service API

**POST /sandbox/create**
```json
{
  "environment": "nodejs-18",
  "timeout": 3600,
  "resources": {
    "cpu": 2,
    "memory": 4096,
    "disk": 10240
  }
}

Response:
{
  "sandbox_id": "sb-abc123",
  "status": "ready",
  "connection": {
    "url": "https://...",
    "token": "..."
  }
}
```

**POST /sandbox/{sandbox_id}/execute**
```json
{
  "files": {
    "server.js": "const express = require('express')...",
    "package.json": "{...}",
    "test.js": "describe('API', () => {...})"
  },
  "commands": [
    "npm install",
    "npm test"
  ],
  "timeout": 300
}

Response:
{
  "execution_id": "exec-xyz789",
  "status": "completed",
  "results": [
    {
      "command": "npm install",
      "exit_code": 0,
      "stdout": "...",
      "stderr": "",
      "duration": 12.5
    },
    {
      "command": "npm test",
      "exit_code": 0,
      "stdout": "✓ 15 tests passed",
      "stderr": "",
      "duration": 3.2,
      "test_results": {
        "total": 15,
        "passed": 15,
        "failed": 0,
        "tests": [...]
      }
    }
  ]
}
```

**GET /sandbox/{sandbox_id}/status**
```json
{
  "sandbox_id": "sb-abc123",
  "status": "running",
  "uptime": 245,
  "resources": {
    "cpu_usage": 45,
    "memory_usage": 1024,
    "disk_usage": 512
  },
  "executions": 5
}
```

**DELETE /sandbox/{sandbox_id}**
```json
{
  "sandbox_id": "sb-abc123",
  "status": "destroyed",
  "total_uptime": 1234,
  "total_executions": 23
}
```

**POST /sandbox/{sandbox_id}/snapshot**
```json
{
  "name": "working-state-feature-5"
}

Response:
{
  "snapshot_id": "snap-def456",
  "size": 2048,
  "created_at": "2025-12-23T14:00:00Z"
}
```

**POST /sandbox/{sandbox_id}/restore**
```json
{
  "snapshot_id": "snap-def456"
}

Response:
{
  "status": "restored",
  "snapshot_id": "snap-def456"
}
```

## Security Considerations

### Network Isolation

**Outbound Access:**
- Allow: npm registry, pip, package managers
- Allow: GitHub, GitLab (for dependencies)
- Block: Internal networks
- Block: Cloud metadata endpoints
- Rate limit: API calls

**Inbound Access:**
- Only from Sandbox Service
- Token-based authentication
- No public internet access

### Resource Limits

```yaml
Per Sandbox:
  CPU: 2 cores max
  Memory: 4GB max
  Disk: 10GB max
  Network: 100Mbps max
  Processes: 100 max
  Open Files: 1024 max
  Execution Time: 1 hour max
```

### Code Restrictions

**Blocked Operations:**
- Kernel module loading
- System calls (ptrace, etc.)
- Device access
- Privileged ports (<1024)
- Fork bombs (process limits)

**Monitored Operations:**
- File system writes (quota)
- Network connections (rate limit)
- CPU usage (throttle)
- Memory allocation (limit)

### Data Protection

**Isolation:**
- Each sandbox has isolated filesystem
- No shared volumes between sandboxes
- Temporary storage only
- Auto-wipe on destroy

**Secrets Management:**
- Environment variables for API keys
- No secrets in code
- Rotate credentials regularly
- Audit access logs

## Implementation Plan

### Phase 1: E2B Integration (Week 1)

**Day 1-2: Sandbox Service**
- Create FastAPI service
- Integrate E2B SDK
- Implement create/execute/destroy endpoints
- Add error handling

**Day 3-4: Coder Integration**
- Update Autonomous Coder to use Sandbox Service
- Implement test result parsing
- Add retry logic for failures
- Update progress tracking

**Day 5: Testing & Documentation**
- End-to-end testing
- Performance testing
- Write integration docs
- Create examples

### Phase 2: Production Hardening (Week 2)

**Day 1-2: Monitoring**
- Add metrics collection
- Implement logging
- Create dashboards
- Set up alerts

**Day 3-4: Optimization**
- Sandbox pooling (pre-warm)
- Caching dependencies
- Parallel test execution
- Cost optimization

**Day 5: Security Audit**
- Penetration testing
- Security review
- Fix vulnerabilities
- Document security model

### Phase 3: Firecracker Migration (Week 3-4)

**Week 3: Setup**
- Provision infrastructure
- Install Firecracker
- Create base images
- Test VM provisioning

**Week 4: Migration**
- Implement Firecracker backend
- Feature parity with E2B
- Gradual traffic migration
- Performance validation

## Cost Analysis

### E2B Costs (100 features/month)

```
Average feature implementation: 10 minutes
Sandbox uptime per feature: 10 minutes
Total sandbox time: 100 × 10 = 1,000 minutes

E2B pricing: ~$0.10-0.30 per hour
Cost: 1,000 min ÷ 60 × $0.20 = $3.33/month
```

**Very affordable for MVP!**

### Firecracker Costs (100 features/month)

```
Infrastructure:
- 1 host server (4 CPU, 16GB RAM): $40/month
- Storage (100GB SSD): $10/month
- Network: $5/month

Total: $55/month

Per-feature cost: $0.55
```

**Better for scale (>100 features/month)**

### Break-even Analysis

```
E2B: $3.33 + $0.033 per feature
Firecracker: $55 fixed

Break-even: 55 ÷ 0.033 ≈ 1,667 features/month

Recommendation:
- <500 features/month: Use E2B
- >500 features/month: Use Firecracker
```

## Monitoring & Observability

### Metrics to Track

**Sandbox Metrics:**
- Sandbox creation time
- Sandbox destruction time
- Active sandboxes count
- Sandbox uptime distribution
- Resource utilization

**Execution Metrics:**
- Test execution time
- Test pass rate
- Failure reasons
- Retry count
- Success rate by feature type

**Cost Metrics:**
- Cost per sandbox
- Cost per feature
- Cost per test
- Monthly total
- Cost trends

### Alerting

**Critical Alerts:**
- Sandbox creation failures
- High failure rate (>20%)
- Resource exhaustion
- Security violations
- Cost spikes

**Warning Alerts:**
- Slow sandbox creation (>30s)
- High resource usage (>80%)
- Long-running sandboxes (>1 hour)
- Unusual network activity

## Testing Strategy

### Unit Tests

```python
# Test sandbox creation
def test_create_sandbox():
    response = client.post("/sandbox/create", json={
        "environment": "nodejs-18"
    })
    assert response.status_code == 200
    assert "sandbox_id" in response.json()

# Test code execution
def test_execute_code():
    sandbox = create_sandbox()
    response = client.post(f"/sandbox/{sandbox['sandbox_id']}/execute", json={
        "files": {"test.js": "console.log('hello')"},
        "commands": ["node test.js"]
    })
    assert response.status_code == 200
    assert "hello" in response.json()["results"][0]["stdout"]
```

### Integration Tests

```python
# Test full feature implementation flow
def test_feature_implementation():
    # 1. Create project
    project = create_project("build hello world API")
    
    # 2. Plan with council
    plan = council.plan(project)
    
    # 3. Create sandbox
    sandbox = sandbox_service.create("nodejs-18")
    
    # 4. Implement in sandbox
    result = coder.implement(plan, sandbox)
    
    # 5. Verify tests pass
    assert result["all_tests_passed"] == True
    
    # 6. Cleanup
    sandbox_service.destroy(sandbox["sandbox_id"])
```

### Load Tests

```python
# Test concurrent sandboxes
def test_concurrent_sandboxes():
    sandboxes = []
    
    # Create 10 sandboxes concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(create_sandbox)
            for _ in range(10)
        ]
        sandboxes = [f.result() for f in futures]
    
    assert len(sandboxes) == 10
    assert all(s["status"] == "ready" for s in sandboxes)
```

## Next Steps

1. **Implement Sandbox Service with E2B** (this week)
2. **Integrate with Autonomous Coder** (this week)
3. **Test with real features** (next week)
4. **Monitor costs and performance** (ongoing)
5. **Plan Firecracker migration** (when scale justifies it)

## References

- [E2B Documentation](https://e2b.dev/docs)
- [Firecracker GitHub](https://github.com/firecracker-microvm/firecracker)
- [Kata Containers](https://katacontainers.io/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
