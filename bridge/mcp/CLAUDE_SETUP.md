# Claude Desktop MCP Setup Guide

## Overview

This guide shows you how to integrate the Code Quality Bridge with Claude Desktop using the Model Context Protocol (MCP).

## What You Get

Once configured, Claude will have access to these tools:

1. **submit_code_for_review** - Send code to Council agents for review
2. **get_review_status** - Check review progress
3. **get_review_report** - Get detailed findings and recommendations
4. **apply_fixes** - Auto-apply suggested fixes
5. **quick_security_scan** - Fast security vulnerability scan
6. **generate_tests** - Generate comprehensive test cases

## Prerequisites

- Claude Desktop installed
- Node.js 18+ installed
- Code Quality Bridge running (see main README)

## Installation

### Step 1: Install MCP Server

```bash
cd /path/to/code-on-fly/bridge/mcp
npm install
```

### Step 2: Make Server Executable

```bash
chmod +x server.js
```

### Step 3: Test Server

```bash
# Set bridge URL
export BRIDGE_URL=http://localhost:8004

# Test server
node server.js
# Should output: "Code Quality Bridge MCP server running on stdio"
# Press Ctrl+C to stop
```

### Step 4: Configure Claude Desktop

**On macOS**:
```bash
# Edit Claude config
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**On Windows**:
```bash
# Edit Claude config
notepad %APPDATA%\Claude\claude_desktop_config.json
```

**On Linux**:
```bash
# Edit Claude config
code ~/.config/Claude/claude_desktop_config.json
```

### Step 5: Add MCP Server Config

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "code-quality-bridge": {
      "command": "node",
      "args": ["/absolute/path/to/code-on-fly/bridge/mcp/server.js"],
      "env": {
        "BRIDGE_URL": "http://localhost:8004",
        "BRIDGE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/` with the actual path on your system.

**Example** (macOS):
```json
{
  "mcpServers": {
    "code-quality-bridge": {
      "command": "node",
      "args": ["/Users/yourname/code-on-fly/bridge/mcp/server.js"],
      "env": {
        "BRIDGE_URL": "http://localhost:8004"
      }
    }
  }
}
```

### Step 6: Restart Claude Desktop

Close and reopen Claude Desktop to load the MCP server.

### Step 7: Verify Integration

In Claude Desktop, type:

```
Can you list your available tools?
```

You should see the 6 code quality tools listed.

## Usage Examples

### Example 1: Basic Code Review

**You**:
```
Review this login function:

function login(username, password) {
  const user = db.query(`SELECT * FROM users WHERE username='${username}'`);
  if (user && user.password === password) {
    return { token: generateToken(user) };
  }
  return null;
}
```

**Claude**:
```
I'll submit this code for review by the Council agents.
*uses submit_code_for_review tool*

Review started! Session ID: rev-abc123

Let me check the status...
*uses get_review_status tool*

The review is in progress. Security agent is analyzing...

*waits a moment*

Review complete! Let me get the report...
*uses get_review_report tool*

# Code Review Report

**Overall Score**: 25/100
**Quality Gate**: FAILED ❌

## Critical Issues Found:

1. **SQL Injection Vulnerability** (Security Agent)
   - Location: line 2
   - The username parameter is directly interpolated into the SQL query
   - Exploit: An attacker could use `' OR '1'='1` to bypass authentication
   - Fix: Use parameterized queries

2. **Plain Text Password Comparison** (Security Agent)
   - Location: line 3
   - Passwords should never be compared in plain text
   - Fix: Use bcrypt or similar hashing algorithm

3. **Missing Tests** (QA Agent)
   - No test cases for authentication failure
   - No test cases for SQL injection attempts
   - No test cases for invalid inputs

## Recommendation:
Fix critical security issues immediately before deployment.

Would you like me to apply the suggested fixes?
```

**You**: "Yes, please fix the critical issues"

**Claude**:
```
*uses apply_fixes tool*

I've applied fixes for the critical issues. Here's the improved code:

function login(username, password) {
  // Input validation
  if (!username || !password) {
    throw new Error('Missing credentials');
  }
  
  // Parameterized query (SQL injection fix)
  const user = db.query(
    'SELECT * FROM users WHERE username = $1',
    [username]
  );
  
  if (!user) {
    return null;
  }
  
  // Hash comparison (password security fix)
  const valid = await bcrypt.compare(password, user.password_hash);
  
  if (valid) {
    return { token: generateToken(user) };
  }
  
  return null;
}

The code now:
✅ Uses parameterized queries to prevent SQL injection
✅ Compares hashed passwords securely
✅ Validates inputs

Would you like me to generate tests for this code?
```

### Example 2: Quick Security Scan

**You**:
```
Can you quickly scan this for security issues?

app.post('/api/data', (req, res) => {
  const query = req.body.query;
  eval(query);
  res.json({ result: 'ok' });
});
```

**Claude**:
```
*uses quick_security_scan tool*

🚨 CRITICAL SECURITY VULNERABILITY DETECTED!

**Code Injection**
- Severity: CRITICAL
- Description: Using eval() on user input allows arbitrary code execution
- Exploit: An attacker could execute `process.exit()` or access sensitive data
- Fix: Never use eval() on user input. Use a safe parser or whitelist approach.

This code should NOT be deployed in its current state.
```

### Example 3: Generate Tests

**You**:
```
Generate tests for this function:

function calculateDiscount(price, discountPercent) {
  return price * (1 - discountPercent / 100);
}
```

**Claude**:
```
*uses generate_tests tool*

Here are comprehensive tests for your discount function:

```javascript
describe('calculateDiscount', () => {
  test('applies 10% discount correctly', () => {
    expect(calculateDiscount(100, 10)).toBe(90);
  });
  
  test('applies 0% discount (no discount)', () => {
    expect(calculateDiscount(100, 0)).toBe(100);
  });
  
  test('applies 100% discount (free)', () => {
    expect(calculateDiscount(100, 100)).toBe(0);
  });
  
  test('handles decimal prices', () => {
    expect(calculateDiscount(99.99, 15)).toBeCloseTo(84.99, 2);
  });
  
  test('handles decimal discount percentages', () => {
    expect(calculateDiscount(100, 12.5)).toBe(87.5);
  });
  
  test('handles negative prices', () => {
    expect(calculateDiscount(-100, 10)).toBe(-90);
  });
  
  test('handles discount over 100%', () => {
    expect(calculateDiscount(100, 150)).toBe(-50);
  });
});
```

**Coverage**: 100% functions, 100% lines, 100% branches

These tests cover:
✅ Normal cases
✅ Edge cases (0%, 100%)
✅ Decimal handling
✅ Negative values
✅ Invalid inputs (>100%)
```

## Advanced Usage

### Custom Quality Gates

You can specify which agents to use:

**You**: "Review this code but only check security and performance"

**Claude**:
```
*uses submit_code_for_review with quality_gates: ["security", "performance"]*
```

### Iterative Improvement

**You**: "Keep reviewing and fixing until the code passes all quality gates"

**Claude** will:
1. Submit code for review
2. Get report
3. Apply fixes
4. Re-submit for review
5. Repeat until quality gates pass

### Batch Review

**You**: "Review all the code files in this project"

**Claude** will:
1. Review each file separately
2. Aggregate findings
3. Prioritize fixes across all files
4. Provide project-wide recommendations

## Troubleshooting

### MCP Server Not Showing Up

**Problem**: Tools not available in Claude

**Solutions**:
1. Check Claude config path is correct
2. Verify absolute path to server.js
3. Restart Claude Desktop
4. Check Claude logs: `~/Library/Logs/Claude/` (macOS)

### Connection Error

**Problem**: "Bridge API error: ECONNREFUSED"

**Solutions**:
1. Ensure Bridge service is running: `curl http://localhost:8004/health`
2. Check BRIDGE_URL in config
3. Verify firewall settings

### Permission Denied

**Problem**: "Permission denied" when running server

**Solution**:
```bash
chmod +x /path/to/bridge/mcp/server.js
```

### Node Version Error

**Problem**: "Unsupported Node version"

**Solution**:
```bash
node --version  # Should be 18+
# If not, install Node 18+
```

## Configuration Options

### Environment Variables

```json
{
  "mcpServers": {
    "code-quality-bridge": {
      "env": {
        "BRIDGE_URL": "http://localhost:8004",
        "BRIDGE_API_KEY": "optional-api-key",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

### Remote Bridge

To use a remote bridge service:

```json
{
  "mcpServers": {
    "code-quality-bridge": {
      "env": {
        "BRIDGE_URL": "https://your-bridge.example.com",
        "BRIDGE_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Best Practices

### 1. Review Before Deployment

Always review code before deploying:
```
"Review this code before I deploy it to production"
```

### 2. Security First

For security-critical code:
```
"Do a thorough security review of this authentication code"
```

### 3. Iterative Development

Use review feedback to improve:
```
"Review this, apply fixes, and review again until it passes"
```

### 4. Learn from Feedback

Pay attention to patterns in feedback to improve your coding.

## Keyboard Shortcuts

In Claude Desktop:

- `Cmd/Ctrl + K` - Quick command
- Type "review" to trigger code review
- Type "scan" for quick security scan
- Type "tests" to generate tests

## Next Steps

1. **Try the examples** above
2. **Review your existing code** to find issues
3. **Use iterative improvement** for complex features
4. **Share feedback** to improve the system

## Support

For issues:
1. Check Bridge service is running
2. Verify Claude config is correct
3. Review MCP server logs
4. Test Bridge API directly

## Updates

To update the MCP server:

```bash
cd /path/to/code-on-fly/bridge/mcp
git pull
npm install
# Restart Claude Desktop
```

## Conclusion

You now have an AI-powered code review assistant integrated directly into Claude Desktop!

**Benefits**:
- ✅ Instant code reviews
- ✅ Security vulnerability detection
- ✅ Automated test generation
- ✅ Quality gates enforcement
- ✅ Iterative improvement

**Happy coding with quality!**
