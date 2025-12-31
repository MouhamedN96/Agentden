# Claude Integration Example

## Setup

1. **Install MCP Server**:
```bash
cd /path/to/code-on-fly/bridge/mcp
npm install
```

2. **Configure Claude Desktop**:

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "code-quality-bridge": {
      "command": "node",
      "args": ["/absolute/path/to/code-on-fly/bridge/mcp/server.js"],
      "env": {
        "BRIDGE_URL": "http://localhost:8004"
      }
    }
  }
}
```

3. **Start Services**:
```bash
cd /path/to/code-on-fly
docker-compose -f docker-compose-bridge.yml up -d
```

4. **Restart Claude Desktop**

## Usage Examples

### Example 1: Basic Code Review

**In Claude Desktop**:

```
User: Review this login function for security issues:

function login(username, password) {
    const user = db.query(`SELECT * FROM users WHERE username='${username}'`);
    if (user && user.password === password) {
        return { token: generateToken(user) };
    }
    return null;
}
```

**Claude will**:
1. Use `submit_code_for_review` tool
2. Wait for review to complete
3. Use `get_review_report` tool
4. Present findings to you

**Expected Output**:
```
I've submitted your code for review by the Council agents. Let me check the results...

# Code Review Report

**Overall Score**: 25/100
**Quality Gate**: FAILED ❌

## Critical Issues:

1. **SQL Injection Vulnerability** (Security Agent)
   - Line 2: Username parameter is directly interpolated into SQL query
   - Exploit: An attacker could use `' OR '1'='1` to bypass authentication
   - Fix: Use parameterized queries

2. **Plain Text Password Comparison** (Security Agent)
   - Line 3: Passwords should never be compared in plain text
   - Fix: Use bcrypt or similar hashing algorithm

3. **Missing Tests** (QA Agent)
   - No test cases for authentication failure
   - No test cases for SQL injection attempts

Would you like me to apply the suggested fixes?
```

### Example 2: Iterative Improvement

**User**: "Yes, please fix the issues and review again"

**Claude will**:
1. Use `apply_fixes` tool to get fixed code
2. Use `submit_code_for_review` again with fixed code
3. Use `get_review_report` to verify fixes

**Expected Output**:
```
I've applied the fixes. Here's the improved code:

```javascript
async function login(username, password) {
    // Input validation
    if (!username || !password) {
        throw new Error('Missing credentials');
    }
    
    // Parameterized query (SQL injection fix)
    const user = await db.query(
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
```

Let me review this again...

# Updated Review Report

**Overall Score**: 85/100
**Quality Gate**: PASSED ✅

The code now:
- Uses parameterized queries (SQL injection fixed)
- Compares hashed passwords securely
- Validates inputs

Remaining recommendations:
- Add rate limiting for login attempts
- Add logging for failed login attempts
- Consider adding 2FA support
```

### Example 3: Quick Security Scan

**User**: "Can you quickly scan this for security issues?"

```javascript
app.post('/api/data', (req, res) => {
    const query = req.body.query;
    eval(query);
    res.json({ result: 'ok' });
});
```

**Claude will**:
1. Use `quick_security_scan` tool
2. Present findings immediately

**Expected Output**:
```
🚨 CRITICAL SECURITY VULNERABILITY DETECTED!

**Code Injection**
- Severity: CRITICAL
- Description: Using eval() on user input allows arbitrary code execution
- Exploit: An attacker could execute `process.exit()` or access sensitive data
- Fix: Never use eval() on user input. Use a safe parser or whitelist approach.

This code should NOT be deployed in its current state.
```

### Example 4: Generate Tests

**User**: "Generate comprehensive tests for this function"

```javascript
function calculateDiscount(price, discountPercent) {
    return price * (1 - discountPercent / 100);
}
```

**Claude will**:
1. Use `generate_tests` tool
2. Present generated test code

**Expected Output**:
```
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
- Normal cases
- Edge cases (0%, 100%)
- Decimal handling
- Negative values
- Invalid inputs (>100%)
```

### Example 5: Continuous Quality

**User**: "Review all my code files and keep fixing until they all pass quality gates"

**Claude will**:
1. Review each file
2. Apply fixes
3. Re-review
4. Repeat until all pass
5. Provide summary

## Tips for Best Results

### 1. Provide Context

Instead of:
```
Review this code
```

Do:
```
Review this authentication code for a banking application. 
Security is critical.
```

### 2. Specify Quality Gates

```
Review this code but only check security and performance
```

Claude will pass `quality_gates: ["security", "performance"]` to the bridge.

### 3. Iterative Development

```
Review this, apply fixes, and review again until it passes all quality gates
```

Claude will loop until quality gates pass.

### 4. Learn from Feedback

Pay attention to recurring issues in reviews to improve your coding patterns.

## Troubleshooting

### Tools Not Available

**Problem**: Claude doesn't show code quality tools

**Solutions**:
1. Check Claude config path is correct
2. Verify absolute path to server.js
3. Restart Claude Desktop
4. Check Claude logs: `~/Library/Logs/Claude/`

### Connection Errors

**Problem**: "Bridge API error: ECONNREFUSED"

**Solutions**:
1. Ensure Bridge service is running:
   ```bash
   curl http://localhost:8004/health
   ```
2. Check docker-compose status:
   ```bash
   docker-compose -f docker-compose-bridge.yml ps
   ```
3. View logs:
   ```bash
   docker-compose -f docker-compose-bridge.yml logs bridge
   ```

### Slow Reviews

**Problem**: Reviews take too long

**Reasons**:
- Council agents are analyzing code (30-60s)
- Sandbox is running tests (30-120s)
- LLM API rate limits

**Solutions**:
- Use `quick_security_scan` for faster security checks
- Reduce quality gates for faster reviews
- Check LLM API status

## Advanced Usage

### Custom Quality Gates

```
Review this code but only run QA and Architecture agents
```

### Batch Processing

```
Review all JavaScript files in this project and create a summary report
```

### Integration with Workflow

```
Before I commit this code, review it and let me know if it's ready
```

## Next Steps

1. Try the examples above
2. Review your existing code
3. Use iterative improvement for complex features
4. Share feedback to improve the system

## Support

For issues:
1. Check Bridge service is running
2. Verify Claude config is correct
3. Review MCP server logs
4. Test Bridge API directly with curl

Happy coding with quality! 🚀
