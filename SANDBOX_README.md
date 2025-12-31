# Sandbox VM Integration for Code-on-Fly

## 🎯 What This Adds

Your Code-on-Fly system now has **real code execution and testing** in isolated sandbox VMs!

### Before Sandbox Integration
```
❌ Simulated test results
❌ No actual code execution
❌ Can't verify code works
❌ No dependency testing
```

### After Sandbox Integration
```
✅ Real code execution in isolated VMs
✅ Actual test validation
✅ Dependency installation verified
✅ Runtime errors caught and fixed
✅ Production-ready code output
```

## 🏗️ Architecture

```
User Request
    ↓
LLM Council Plans
    ↓
Autonomous Coder Generates Code
    ↓
┌─────────────────────────────┐
│   Sandbox Service (NEW)     │
│   - Creates VM              │
│   - Executes code           │
│   - Runs tests              │
│   - Returns results         │
└─────────────────────────────┘
    ↓
Real Test Results
    ↓
If tests fail → Fix code → Retry
If tests pass → Mark complete ✅
```

## 📦 What's Included

### New Components

1. **Sandbox Service** (`sandbox/main.py`)
   - Port: 8003
   - Orchestrates E2B sandbox VMs
   - Executes code and runs tests
   - Parses test results

2. **Updated Coder Service** (`coder/main_with_sandbox.py`)
   - Integrates with Sandbox Service
   - Receives real test results
   - Iterates on failures
   - Only marks complete when tests pass

3. **Docker Compose** (`docker-compose-with-sandbox.yml`)
   - Adds sandbox service
   - Configures networking
   - Sets up dependencies

### Documentation

1. **Architecture Guide** (`docs/SANDBOX_ARCHITECTURE.md`)
   - Design decisions
   - Technology comparison
   - Security considerations
   - Cost analysis

2. **Integration Guide** (`docs/SANDBOX_INTEGRATION_GUIDE.md`)
   - Step-by-step setup
   - Usage examples
   - Troubleshooting
   - Migration path

3. **Testing Script** (`examples/test_sandbox_integration.py`)
   - Comprehensive test suite
   - Validates integration
   - Provides examples

## 🚀 Quick Start

### Step 1: Get E2B API Key

```bash
# 1. Go to https://e2b.dev
# 2. Sign up for free account
# 3. Create API key
# 4. Copy key (starts with e2b_)
```

### Step 2: Update Environment

Add to `.env`:

```bash
# E2B Sandbox Configuration
E2B_API_KEY=e2b_your_api_key_here
SANDBOX_SERVICE_URL=http://localhost:8003
```

### Step 3: Start Services

```bash
# Start all services including sandbox
docker-compose -f docker-compose-with-sandbox.yml up -d

# Check logs
docker-compose -f docker-compose-with-sandbox.yml logs -f

# Verify services
curl http://localhost:8003/health  # Sandbox
curl http://localhost:8002/health  # Coder
```

### Step 4: Test Integration

```bash
# Run test suite
python3 examples/test_sandbox_integration.py

# Expected output:
# ✓ Sandbox service healthy
# ✓ Coder service healthy
# ✓ Sandbox created
# ✓ Code executed successfully
# ✓ Tests passed
# 🎉 All tests passed!
```

### Step 5: Try It!

In Slack:
```
/code-team build a function that adds two numbers with tests
```

Watch the logs to see:
1. ✅ Council plans implementation
2. ✅ Sandbox VM created
3. ✅ Code generated
4. ✅ Tests executed in sandbox
5. ✅ Tests pass
6. ✅ Feature marked complete
7. ✅ Sandbox cleaned up

## 💡 Usage Examples

### Example 1: Simple Function

**Request**: "Build a function that multiplies two numbers"

**What Happens**:

1. **Code Generated**:
   ```javascript
   // multiply.js
   function multiply(a, b) {
     return a * b;
   }
   module.exports = { multiply };
   ```

2. **Tests Generated**:
   ```javascript
   // multiply.test.js
   const { multiply } = require('./multiply');
   
   test('multiplies positive numbers', () => {
     expect(multiply(2, 3)).toBe(6);
   });
   
   test('multiplies by zero', () => {
     expect(multiply(5, 0)).toBe(0);
   });
   ```

3. **Sandbox Executes**:
   ```bash
   npm install
   npm test
   ```

4. **Result**: ✅ 2 tests passed

### Example 2: Bug Detection & Fix

**Request**: "Build a function that calculates factorial"

**Attempt 1** (Bug):
```javascript
function factorial(n) {
  if (n === 0) return 1;
  return n * factorial(n - 1);
}
```

**Test Fails**: ❌ "factorial(-1) causes stack overflow"

**Attempt 2** (Fixed):
```javascript
function factorial(n) {
  if (n < 0) throw new Error('Negative numbers not allowed');
  if (n === 0) return 1;
  return n * factorial(n - 1);
}
```

**Test Passes**: ✅ All edge cases handled

### Example 3: Complex Feature

**Request**: "Build Express API for user registration"

**Generated**:
- `package.json` (express, bcrypt, jest)
- `server.js` (Express app)
- `routes/auth.js` (Registration endpoint)
- `models/user.js` (User model)
- `server.test.js` (Integration tests)

**Sandbox Executes**:
```bash
npm install  # Installs all dependencies
npm test     # Runs integration tests
```

**Tests Verify**:
- ✅ POST /register endpoint works
- ✅ Password hashing works
- ✅ Duplicate email validation
- ✅ JWT token generation

**Result**: ✅ Production-ready API

## 📊 Cost Analysis

### E2B Pricing

**Sandbox Runtime**: ~$0.10-0.30 per hour

**Typical Usage**:
- Feature implementation: 5-10 minutes
- Cost per feature: $0.01-0.05

**Monthly Estimate** (100 features):
- Average 7 minutes per feature
- Total: 700 minutes = 11.7 hours
- **Cost: $2.34/month**

**Very affordable!**

### Cost Comparison

| Solution | Setup | Monthly (100 features) |
|----------|-------|----------------------|
| E2B | 5 minutes | $2-5 |
| Firecracker | 2 days | $55 (fixed) |
| Docker | 1 hour | $40 (fixed) |

**Recommendation**: Start with E2B, migrate to Firecracker at scale.

## 🔒 Security Features

### Isolation
- ✅ Each sandbox is completely isolated
- ✅ No access to host system
- ✅ No access to other sandboxes
- ✅ Auto-cleanup after use

### Resource Limits
- CPU: 2 cores max
- Memory: 4GB max
- Disk: 10GB max
- Execution time: 1 hour max

### Network Security
- ✅ Outbound: npm, pip, GitHub only
- ❌ Blocked: Internal networks
- ❌ Blocked: Cloud metadata endpoints
- ✅ Rate limited: API calls

### Code Restrictions
- ❌ Blocked: Kernel modules
- ❌ Blocked: System calls
- ❌ Blocked: Device access
- ❌ Blocked: Privileged ports

## 🛠️ Supported Environments

### Node.js 18
```json
{
  "environment": "nodejs-18"
}
```
- Pre-installed: Node.js 18.x, npm
- Test command: `npm test`
- Popular packages: express, jest, etc.

### Python 3.11
```json
{
  "environment": "python-3.11"
}
```
- Pre-installed: Python 3.11, pip
- Test command: `pytest`
- Popular packages: pytest, requests, etc.

### Go 1.21
```json
{
  "environment": "go-1.21"
}
```
- Pre-installed: Go 1.21
- Test command: `go test`

## 📈 Monitoring

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

### View Execution Logs

```bash
# Coder service logs
docker logs autonomous-coder -f

# Look for:
# ✓ Tests passed!
#   Total: 5, Passed: 5, Failed: 0
```

### Track Costs

```bash
# Get all sandboxes
curl http://localhost:8003/sandboxes | jq '.sandboxes'

# Calculate total uptime
curl http://localhost:8003/sandboxes | \
  jq '[.sandboxes[].uptime] | add / 3600 * 0.20'
# Output: estimated cost in dollars
```

## 🐛 Troubleshooting

### Sandbox Creation Fails

**Error**: "Failed to create sandbox"

**Fix**:
```bash
# Check E2B API key
echo $E2B_API_KEY

# Test E2B directly
curl -X POST https://api.e2b.dev/sandboxes \
  -H "Authorization: Bearer $E2B_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"template": "base"}'
```

### Tests Keep Failing

**Error**: "Tests failed after 3 attempts"

**Fix**:
```bash
# Check error messages
docker logs autonomous-coder | grep "stderr:"

# Test manually in sandbox
SANDBOX_ID="sb-xxx"
curl -X POST http://localhost:8003/sandbox/$SANDBOX_ID/execute \
  -H "Content-Type: application/json" \
  -d '{
    "files": {"test.js": "console.log(\"test\");"},
    "commands": ["node test.js"]
  }'
```

### Sandbox Not Cleaned Up

**Error**: Sandbox still running

**Fix**:
```bash
# List all sandboxes
curl http://localhost:8003/sandboxes

# Delete specific sandbox
curl -X DELETE http://localhost:8003/sandbox/sb-xxx

# Delete all sandboxes
for id in $(curl -s http://localhost:8003/sandboxes | jq -r '.sandboxes[].sandbox_id'); do
  curl -X DELETE http://localhost:8003/sandbox/$id
done
```

## 🔄 Migration Path

### From Old Coder to New Coder

**Option 1: Direct Replacement**
```bash
# Stop old services
docker-compose down

# Start new services with sandbox
docker-compose -f docker-compose-with-sandbox.yml up -d
```

**Option 2: Gradual Migration**
```bash
# Run both versions
docker-compose up -d  # Old coder on 8002
docker-compose -f docker-compose-with-sandbox.yml up coder  # New on 8004

# Update n8n to use new coder for specific projects
# Gradually migrate all projects
# Shut down old coder
```

## 📚 API Reference

### Sandbox Service API

**Create Sandbox**
```bash
POST /sandbox/create
{
  "environment": "nodejs-18",
  "timeout": 3600
}
```

**Execute Code**
```bash
POST /sandbox/{sandbox_id}/execute
{
  "files": {"main.js": "console.log('hello');"},
  "commands": ["node main.js"],
  "timeout": 300
}
```

**Get Status**
```bash
GET /sandbox/{sandbox_id}/status
```

**Destroy Sandbox**
```bash
DELETE /sandbox/{sandbox_id}
```

**List Sandboxes**
```bash
GET /sandboxes
```

## 🎓 Best Practices

### 1. Reuse Sandboxes
```python
# Create once per project, not per feature
sandbox = create_sandbox()
for feature in features:
    execute_in_sandbox(sandbox, feature)
destroy_sandbox(sandbox)
```

### 2. Set Appropriate Timeouts
```python
# Short timeout for simple tests
timeout = 60  # 1 minute

# Longer timeout for complex features
timeout = 300  # 5 minutes
```

### 3. Handle Failures Gracefully
```python
max_retries = 3
for attempt in range(max_retries):
    result = execute_tests()
    if result.success:
        break
    if attempt < max_retries - 1:
        analyze_error_and_fix()
```

### 4. Clean Up Resources
```python
try:
    sandbox = create_sandbox()
    implement_features(sandbox)
finally:
    destroy_sandbox(sandbox)  # Always cleanup
```

## 🚀 Next Steps

1. **Test with simple features** to validate setup
2. **Monitor costs** and optimize as needed
3. **Add more environments** (Rust, Java, etc.)
4. **Implement caching** for dependencies
5. **Add metrics** for success rate tracking
6. **Consider Firecracker** for self-hosted at scale

## 📖 Documentation

- [Sandbox Architecture](docs/SANDBOX_ARCHITECTURE.md) - Design and technology choices
- [Integration Guide](docs/SANDBOX_INTEGRATION_GUIDE.md) - Detailed setup and usage
- [Main README](README.md) - Overall Code-on-Fly documentation
- [Implementation Guide](IMPLEMENTATION_GUIDE.md) - Complete setup guide

## 🤝 Support

For issues:
1. Check service logs: `docker-compose logs`
2. Run test suite: `python3 examples/test_sandbox_integration.py`
3. Review documentation
4. Check E2B status: https://status.e2b.dev

## 🎉 Summary

You now have a **production-grade autonomous coding system** with:

✅ **Real code execution** in isolated VMs
✅ **Actual test validation** with retry logic
✅ **Security isolation** with resource limits
✅ **Cost-effective** (~$2-5/month for 100 features)
✅ **Multi-language support** (Node.js, Python, Go)
✅ **Production-ready** code output

**The future of autonomous coding is here. Your agents can now write, test, and validate code automatically!**
