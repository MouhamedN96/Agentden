# Sandbox Integration Guide

## Overview

This guide explains how to set up and use the sandbox VM integration in Code-on-Fly, enabling autonomous agents to safely execute and test code in isolated environments.

## What Changed

### Before Sandbox Integration

```
User Request → Council Plans → Coder Generates Code → Mark Complete
                                        ↓
                              (No actual testing)
```

**Problems:**
- ❌ No real code execution
- ❌ No test validation
- ❌ Can't verify code actually works
- ❌ No dependency installation testing
- ❌ No runtime error detection

### After Sandbox Integration

```
User Request → Council Plans → Coder Generates Code → Sandbox Executes → Tests Run → Mark Complete
                                        ↓                    ↓              ↓
                                   Real Files         Real Environment   Real Results
```

**Benefits:**
- ✅ Real code execution in isolated VMs
- ✅ Actual test validation
- ✅ Dependency installation verified
- ✅ Runtime errors caught and fixed
- ✅ Production-ready code output

## Architecture

### New Component: Sandbox Service

**Purpose**: Orchestrate sandbox VMs for code execution

**Technology**: E2B (cloud sandboxes) or Firecracker (self-hosted)

**Port**: 8003

**Responsibilities**:
- Create/destroy sandbox VMs
- Execute code in sandboxes
- Run tests and collect results
- Parse test output
- Manage sandbox lifecycle

### Updated Component: Autonomous Coder

**Changes**:
- Now calls Sandbox Service instead of simulating tests
- Receives real test results
- Iterates on failures with actual error messages
- Marks features complete only when tests pass

### Data Flow

```
1. Coder generates code for feature
   ↓
2. Coder → Sandbox Service: "Create sandbox"
   ↓
3. Sandbox Service → E2B: Provision VM
   ↓
4. Coder → Sandbox Service: "Execute code + tests"
   ↓
5. Sandbox Service → E2B: Write files, run commands
   ↓
6. E2B → Sandbox Service: stdout, stderr, exit code
   ↓
7. Sandbox Service → Coder: Parsed test results
   ↓
8. If tests fail:
   - Coder analyzes errors
   - Generates fix
   - Repeat from step 4
   ↓
9. If tests pass:
   - Mark feature complete
   - Move to next feature
   ↓
10. Coder → Sandbox Service: "Destroy sandbox"
```

## Setup Instructions

### Step 1: Get E2B API Key

1. Go to [https://e2b.dev](https://e2b.dev)
2. Sign up for an account
3. Navigate to API Keys
4. Create new API key
5. Copy the key (starts with `e2b_`)

**Pricing**: ~$0.10-0.30 per hour per sandbox
**Free tier**: Available for testing

### Step 2: Update Environment Variables

Add to your `.env` file:

```bash
# E2B Configuration
E2B_API_KEY=e2b_your_api_key_here

# Sandbox Service URL (for local development)
SANDBOX_SERVICE_URL=http://localhost:8003
```

### Step 3: Create Sandbox Service Dockerfile

Create `sandbox/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8003

CMD ["python", "main.py"]
```

Create `sandbox/requirements.txt`:

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
pydantic==2.5.3
python-dotenv==1.0.0
```

### Step 4: Update Coder Service Dockerfile

Create `coder/Dockerfile.sandbox`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Use the sandbox-enabled version
COPY main_with_sandbox.py main.py

EXPOSE 8002

CMD ["python", "main.py"]
```

### Step 5: Start Services

```bash
# Use the new docker-compose file
docker-compose -f docker-compose-with-sandbox.yml up -d

# Check logs
docker-compose -f docker-compose-with-sandbox.yml logs -f

# Verify all services are healthy
docker-compose -f docker-compose-with-sandbox.yml ps
```

### Step 6: Test Sandbox Service

```bash
# Test sandbox creation
curl -X POST http://localhost:8003/sandbox/create \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "nodejs-18",
    "timeout": 3600
  }'

# Response:
# {
#   "sandbox_id": "sb-abc123",
#   "status": "ready",
#   "connection": {...},
#   "created_at": "2025-12-23T15:00:00Z"
# }

# Test code execution
SANDBOX_ID="sb-abc123"  # Use ID from above

curl -X POST http://localhost:8003/sandbox/$SANDBOX_ID/execute \
  -H "Content-Type: application/json" \
  -d '{
    "files": {
      "test.js": "console.log(\"Hello from sandbox!\");"
    },
    "commands": ["node test.js"],
    "timeout": 60
  }'

# Response:
# {
#   "execution_id": "exec-xyz789",
#   "status": "completed",
#   "results": [
#     {
#       "command": "node test.js",
#       "exit_code": 0,
#       "stdout": "Hello from sandbox!\n",
#       "stderr": "",
#       "duration": 0.5
#     }
#   ]
# }

# Clean up
curl -X DELETE http://localhost:8003/sandbox/$SANDBOX_ID
```

### Step 7: Test End-to-End

```bash
# In Slack, request a simple feature
/code-team build a hello world API endpoint

# Watch the logs to see:
# 1. Council planning
# 2. Sandbox creation
# 3. Code generation
# 4. Test execution in sandbox
# 5. Test results
# 6. Feature completion
# 7. Sandbox cleanup
```

## Usage Examples

### Example 1: Simple Node.js Feature

**Request**: "Build a function that adds two numbers"

**What happens**:

1. **Council plans**:
   - Feature: Addition function
   - Tests: Test with positive, negative, zero

2. **Coder generates**:
   ```javascript
   // add.js
   module.exports = function add(a, b) {
     return a + b;
   };
   ```
   
   ```javascript
   // add.test.js
   const add = require('./add');
   
   test('adds positive numbers', () => {
     expect(add(2, 3)).toBe(5);
   });
   
   test('adds negative numbers', () => {
     expect(add(-2, -3)).toBe(-5);
   });
   
   test('adds with zero', () => {
     expect(add(5, 0)).toBe(5);
   });
   ```

3. **Sandbox executes**:
   ```bash
   npm install
   npm test
   ```

4. **Results**:
   ```
   ✓ adds positive numbers
   ✓ adds negative numbers
   ✓ adds with zero
   
   Tests: 3 passed, 3 total
   ```

5. **Feature marked complete** ✅

### Example 2: Feature with Bug

**Request**: "Build a function that divides two numbers"

**Attempt 1**:

```javascript
// divide.js
module.exports = function divide(a, b) {
  return a / b;
};
```

**Test fails**:
```
✗ handles division by zero
  Expected: Error
  Received: Infinity
```

**Coder analyzes error, generates fix**:

```javascript
// divide.js (fixed)
module.exports = function divide(a, b) {
  if (b === 0) {
    throw new Error('Division by zero');
  }
  return a / b;
};
```

**Test passes** ✅

### Example 3: Complex Feature with Dependencies

**Request**: "Build an Express API endpoint for user registration"

**Generated files**:
- `package.json` (with express, bcrypt, etc.)
- `server.js` (Express app)
- `routes/auth.js` (Registration endpoint)
- `models/user.js` (User model)
- `server.test.js` (Integration tests)

**Sandbox executes**:
```bash
npm install  # Installs express, bcrypt, jest, supertest
npm test     # Runs integration tests
```

**Tests verify**:
- ✅ Endpoint responds to POST /register
- ✅ Password is hashed
- ✅ Duplicate emails are rejected
- ✅ Returns JWT token

**All tests pass** → Feature complete ✅

## Supported Environments

### Node.js 18

**Template**: `nodejs-18`

**Pre-installed**:
- Node.js 18.x
- npm
- Common packages: express, jest, etc.

**Test command**: `npm test`

**Example**:
```json
{
  "environment": "nodejs-18"
}
```

### Python 3.11

**Template**: `python-3.11`

**Pre-installed**:
- Python 3.11
- pip
- Common packages: pytest, requests, etc.

**Test command**: `pytest`

**Example**:
```json
{
  "environment": "python-3.11"
}
```

### Go 1.21

**Template**: `go-1.21`

**Pre-installed**:
- Go 1.21
- go test

**Test command**: `go test`

**Example**:
```json
{
  "environment": "go-1.21"
}
```

## Monitoring & Debugging

### Check Active Sandboxes

```bash
curl http://localhost:8003/sandboxes
```

**Response**:
```json
{
  "sandboxes": [
    {
      "sandbox_id": "sb-abc123",
      "status": "ready",
      "environment": "nodejs-18",
      "uptime": 245,
      "executions": 5
    }
  ]
}
```

### Check Sandbox Status

```bash
curl http://localhost:8003/sandbox/sb-abc123/status
```

**Response**:
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

### View Execution Results

Check the coder service logs:

```bash
docker logs autonomous-coder -f
```

Look for:
```
==========================================================
Implementing: Build addition function
==========================================================
Attempt 1/3: Running tests in sandbox...
✓ Tests passed!
  Total: 3, Passed: 3, Failed: 0
```

### Debug Failed Tests

If tests fail, check:

1. **Execution logs**:
   ```bash
   docker logs autonomous-coder | grep "✗"
   ```

2. **Error messages**:
   ```bash
   docker logs autonomous-coder | grep "stderr:"
   ```

3. **Sandbox status**:
   ```bash
   curl http://localhost:8003/sandboxes
   ```

## Cost Management

### E2B Pricing

**Sandbox uptime**: ~$0.10-0.30 per hour

**Typical feature**: 5-10 minutes
**Cost per feature**: ~$0.01-0.05

**Monthly estimate** (100 features):
- Average 7 minutes per feature
- Total: 700 minutes = 11.7 hours
- Cost: 11.7 × $0.20 = **$2.34/month**

**Very affordable!**

### Optimization Tips

1. **Reuse sandboxes** for multiple features
   - Keep sandbox alive for entire project
   - Only create new sandbox per project, not per feature

2. **Parallel execution**
   - Run multiple sandboxes for different projects
   - Faster overall, same cost

3. **Timeout management**
   - Set appropriate timeouts
   - Auto-cleanup idle sandboxes

4. **Caching**
   - Cache npm/pip installs
   - Reuse dependencies across features

### Cost Monitoring

Track costs in your code:

```python
# In sandbox service
total_uptime = sum(
    sandbox["uptime"]
    for sandbox in active_sandboxes.values()
)

estimated_cost = (total_uptime / 3600) * 0.20  # $0.20/hour
print(f"Estimated cost: ${estimated_cost:.2f}")
```

## Security Considerations

### Network Isolation

**E2B sandboxes are isolated by default:**
- ✅ No access to internal networks
- ✅ No access to cloud metadata endpoints
- ✅ Rate-limited external API calls
- ✅ Blocked malicious domains

**Additional security**:
- Don't pass secrets in code
- Use environment variables for API keys
- Rotate credentials regularly

### Resource Limits

**Per sandbox**:
- CPU: 2 cores max
- Memory: 4GB max
- Disk: 10GB max
- Execution time: 1 hour max

**Enforced by E2B automatically**

### Code Restrictions

**Blocked operations**:
- Kernel module loading
- System calls (ptrace, etc.)
- Device access
- Privileged ports (<1024)

**Monitored operations**:
- File system writes (quota)
- Network connections (rate limit)
- CPU usage (throttle)

## Troubleshooting

### Sandbox Creation Fails

**Error**: "Failed to create sandbox"

**Solutions**:
1. Check E2B API key is valid
2. Verify E2B account has credits
3. Check network connectivity
4. Review E2B service status

```bash
# Test E2B API directly
curl -X POST https://api.e2b.dev/sandboxes \
  -H "Authorization: Bearer $E2B_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"template": "base"}'
```

### Code Execution Timeout

**Error**: "Execution timed out"

**Solutions**:
1. Increase timeout in request
2. Optimize code (reduce dependencies)
3. Check for infinite loops
4. Review sandbox logs

```bash
# Increase timeout
curl -X POST http://localhost:8003/sandbox/$SANDBOX_ID/execute \
  -d '{
    "files": {...},
    "commands": [...],
    "timeout": 600  # 10 minutes
  }'
```

### Tests Keep Failing

**Error**: "Tests failed after 3 attempts"

**Solutions**:
1. Check test expectations are correct
2. Review error messages in logs
3. Verify dependencies are installed
4. Test code manually in sandbox

```bash
# Manual testing
curl -X POST http://localhost:8003/sandbox/$SANDBOX_ID/execute \
  -d '{
    "files": {"test.js": "console.log(process.version);"},
    "commands": ["node test.js"]
  }'
```

### Sandbox Not Destroyed

**Error**: Sandbox still running after session complete

**Solutions**:
1. Manually destroy sandbox
2. Check auto-cleanup task
3. Review background task logs

```bash
# Manual cleanup
curl -X DELETE http://localhost:8003/sandbox/$SANDBOX_ID

# List all sandboxes
curl http://localhost:8003/sandboxes

# Destroy all
for id in $(curl -s http://localhost:8003/sandboxes | jq -r '.sandboxes[].sandbox_id'); do
  curl -X DELETE http://localhost:8003/sandbox/$id
done
```

## Migration from Old Coder

### Option 1: Side-by-Side

Run both old and new coder services:

```yaml
# docker-compose.yml
services:
  coder-old:
    # Old coder without sandbox
    ports:
      - "8002:8002"
  
  coder-new:
    # New coder with sandbox
    ports:
      - "8004:8002"
```

Test with new coder, fallback to old if needed.

### Option 2: Feature Flag

Add feature flag to n8n workflow:

```javascript
// In n8n workflow
const useSandbox = $env.USE_SANDBOX === 'true';
const coderUrl = useSandbox 
  ? 'http://coder-new:8002' 
  : 'http://coder-old:8002';
```

Gradually enable for more projects.

### Option 3: Direct Replacement

Replace old coder with new one:

```bash
# Stop old coder
docker stop autonomous-coder

# Start new coder with sandbox
docker-compose -f docker-compose-with-sandbox.yml up -d coder
```

## Next Steps

1. **Test with simple features** to validate setup
2. **Monitor costs** and optimize as needed
3. **Add more environments** (Rust, Java, etc.)
4. **Implement caching** for faster execution
5. **Add metrics** for success rate tracking
6. **Consider Firecracker** for self-hosted option

## References

- [E2B Documentation](https://e2b.dev/docs)
- [Sandbox Architecture](./SANDBOX_ARCHITECTURE.md)
- [Code-on-Fly README](../README.md)
- [Implementation Guide](../IMPLEMENTATION_GUIDE.md)
