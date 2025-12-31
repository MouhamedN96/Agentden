# Bridge System Quick Start Guide

Get your AI coding assistant connected to quality review agents in 10 minutes.

## What You're Building

A system where Claude (or any AI assistant) can automatically:
- Review code for security vulnerabilities
- Generate comprehensive tests
- Check performance issues
- Apply fixes automatically
- Enforce quality gates

## Prerequisites

Install these first:
- Docker Desktop
- Node.js 18+
- Git

Get API keys:
- OpenRouter: https://openrouter.ai (for LLM access)
- E2B: https://e2b.dev (for sandboxes)

## Step 1: Setup (5 minutes)

```bash
# Navigate to project
cd code-on-fly

# Create environment file
cat > .env << EOF
OPENROUTER_API_KEY=your_openrouter_key_here
E2B_API_KEY=your_e2b_key_here
EOF

# Start all services
docker-compose -f docker-compose-bridge.yml up -d

# Wait 30 seconds for services to start
sleep 30

# Verify services are running
curl http://localhost:8004/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "bridge",
  "timestamp": "2024-..."
}
```

## Step 2: Test with API (2 minutes)

Create a test file `test_review.sh`:

```bash
#!/bin/bash

# Submit code for review
RESPONSE=$(curl -s -X POST http://localhost:8004/api/v1/review/submit \
  -H "Content-Type: application/json" \
  -d '{
    "code": "function login(username, password) { const user = db.query(`SELECT * FROM users WHERE username='\''${username}'\''`); if (user && user.password === password) { return { token: generateToken(user) }; } return null; }",
    "language": "javascript",
    "context": "User authentication",
    "quality_gates": ["security", "qa"]
  }')

echo "Response: $RESPONSE"

# Extract session ID
SESSION_ID=$(echo $RESPONSE | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
echo "Session ID: $SESSION_ID"

# Wait for review to complete
echo "Waiting for review..."
sleep 60

# Get report
curl -s http://localhost:8004/api/v1/review/$SESSION_ID/report | jq '.'
```

Run it:
```bash
chmod +x test_review.sh
./test_review.sh
```

You should see security vulnerabilities detected!

## Step 3: Connect Claude Desktop (3 minutes)

### Install MCP Server

```bash
cd bridge/mcp
npm install
```

### Configure Claude

**On macOS**:
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**On Windows**:
```bash
notepad %APPDATA%\Claude\claude_desktop_config.json
```

Add this configuration:

```json
{
  "mcpServers": {
    "code-quality-bridge": {
      "command": "node",
      "args": ["/FULL/PATH/TO/code-on-fly/bridge/mcp/server.js"],
      "env": {
        "BRIDGE_URL": "http://localhost:8004"
      }
    }
  }
}
```

**Important**: Replace `/FULL/PATH/TO/` with your actual path!

**Example** (macOS):
```json
{
  "mcpServers": {
    "code-quality-bridge": {
      "command": "node",
      "args": ["/Users/john/code-on-fly/bridge/mcp/server.js"],
      "env": {
        "BRIDGE_URL": "http://localhost:8004"
      }
    }
  }
}
```

### Restart Claude Desktop

Close and reopen Claude Desktop completely.

### Test Integration

In Claude Desktop, type:

```
Can you list your available tools?
```

You should see 6 code quality tools listed!

## Step 4: Use It! (1 minute)

In Claude Desktop, paste this:

```
Review this code for security issues:

function login(username, password) {
    const user = db.query(`SELECT * FROM users WHERE username='${username}'`);
    if (user && user.password === password) {
        return { token: generateToken(user) };
    }
    return null;
}
```

Claude will:
1. Submit code to Bridge
2. Wait for Council review
3. Show you the security vulnerabilities
4. Offer to fix them

## What Just Happened?

```
You → Claude Desktop → MCP Server → Bridge Service
                                        ↓
                                  Council Agents
                                  (QA, Security, Performance)
                                        ↓
                                  Sandbox VMs
                                  (Execute & Test)
                                        ↓
                                  Quality Report → Claude → You
```

## Common Issues

### "Connection refused"

**Problem**: Services not running

**Fix**:
```bash
docker-compose -f docker-compose-bridge.yml ps
docker-compose -f docker-compose-bridge.yml up -d
```

### "Tools not showing in Claude"

**Problem**: MCP not configured correctly

**Fix**:
1. Check path in config is absolute (not relative)
2. Restart Claude Desktop completely
3. Check logs: `~/Library/Logs/Claude/`

### "Review taking too long"

**Normal**: Reviews take 60-120 seconds
- Council agents analyze code: 30-60s
- Sandbox runs tests: 30-60s

**If stuck**:
```bash
# Check logs
docker-compose -f docker-compose-bridge.yml logs bridge
docker-compose -f docker-compose-bridge.yml logs council
```

## Next Steps

### Try More Features

**Generate tests**:
```
Generate comprehensive tests for this function:

function calculateDiscount(price, discountPercent) {
    return price * (1 - discountPercent / 100);
}
```

**Quick security scan**:
```
Quick security scan on this:

app.post('/api/data', (req, res) => {
    eval(req.body.query);
});
```

**Iterative improvement**:
```
Review this code, apply fixes, and review again until it passes all quality gates
```

### Explore Examples

```bash
cd bridge/examples
cat claude_example.md
```

### Run Tests

```bash
cd bridge
python test_bridge.py
```

### Read Documentation

```bash
cd bridge
cat README.md
```

## Usage Tips

### 1. Provide Context

Good:
```
Review this authentication code for a banking app. Security is critical.
```

Better than:
```
Review this code
```

### 2. Specify Quality Gates

```
Review this but only check security and performance
```

### 3. Iterative Development

```
Keep reviewing and fixing until this passes all quality gates
```

## Cost Estimate

**Per Review**:
- LLM API: $0.05-0.15
- Sandbox: $0.01-0.05
- Total: $0.06-0.20

**Monthly** (100 reviews):
- $17-40/month

Very affordable for the value!

## Getting Help

**Check service health**:
```bash
curl http://localhost:8004/health
curl http://localhost:8001/health
curl http://localhost:8003/health
```

**View logs**:
```bash
docker-compose -f docker-compose-bridge.yml logs -f
```

**Restart services**:
```bash
docker-compose -f docker-compose-bridge.yml restart
```

**Stop services**:
```bash
docker-compose -f docker-compose-bridge.yml down
```

## What's Next?

You now have:
- ✅ Automated code review
- ✅ Security vulnerability detection
- ✅ Test generation
- ✅ Quality gates enforcement
- ✅ Claude integration

**Enhance your workflow**:
1. Review all your existing code
2. Use before every commit
3. Enforce quality gates in CI/CD
4. Share with your team

## Support

- Documentation: `bridge/README.md`
- Examples: `bridge/examples/`
- Tests: `bridge/test_bridge.py`
- Architecture: `docs/BRIDGE_ARCHITECTURE.md`

Happy coding with quality! 🚀
