# Code Quality Bridge

Bridge your AI coding assistant (Claude, Manus, Gemini, etc.) with specialized Council agents for automated code review, security scanning, and quality assurance.

## What It Does

The Bridge connects your AI coding workflow with a team of specialized agents that review your code for:

- **Security vulnerabilities** (SQL injection, XSS, auth bypass, prompt injection)
- **Quality issues** (missing tests, edge cases, error handling)
- **Performance problems** (N+1 queries, inefficient algorithms, memory leaks)
- **Architecture concerns** (design patterns, SOLID principles, code smells)

## Architecture

```
Claude/Manus/Gemini → Bridge Service → Council Agents → Sandbox VMs → Quality Report
```

**Components**:
- **Bridge Service** (Port 8004): REST API + WebSocket + MCP server
- **Council Service** (Port 8001): QA, Security, Performance, Architecture agents
- **Sandbox Service** (Port 8003): Isolated VMs for code execution and testing
- **Redis**: Session storage and caching

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for MCP server)
- OpenRouter API key
- E2B API key (for sandboxes)

### 1. Clone and Configure

```bash
cd code-on-fly/bridge

# Create .env file
cat > .env << EOF
OPENROUTER_API_KEY=your_openrouter_key
E2B_API_KEY=your_e2b_key
EOF
```

### 2. Start Services

```bash
cd ..
docker-compose -f docker-compose-bridge.yml up -d
```

### 3. Verify Services

```bash
# Check all services are healthy
docker-compose -f docker-compose-bridge.yml ps

# Test Bridge API
curl http://localhost:8004/health
```

### 4. Configure Claude Desktop (Optional)

For native Claude integration:

```bash
cd bridge/mcp
npm install
```

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Restart Claude Desktop.

## Usage

### Via Claude Desktop (MCP)

In Claude Desktop, simply ask:

```
Review this login function for security issues:

function login(username, password) {
    const user = db.query(`SELECT * FROM users WHERE username='${username}'`);
    if (user && user.password === password) {
        return { token: generateToken(user) };
    }
    return null;
}
```

Claude will automatically use the Bridge tools to review your code.

### Via REST API

**Submit code for review**:

```bash
curl -X POST http://localhost:8004/api/v1/review/submit \
  -H "Content-Type: application/json" \
  -d '{
    "code": "function login(username, password) { ... }",
    "language": "javascript",
    "context": "User authentication",
    "quality_gates": ["qa", "security"]
  }'
```

Response:
```json
{
  "session_id": "rev-abc123",
  "status": "pending",
  "message": "Review started"
}
```

**Check status**:

```bash
curl http://localhost:8004/api/v1/review/rev-abc123/status
```

**Get report**:

```bash
curl http://localhost:8004/api/v1/review/rev-abc123/report
```

**Apply fixes**:

```bash
curl -X POST http://localhost:8004/api/v1/review/rev-abc123/fix \
  -H "Content-Type: application/json" \
  -d '{"fix_priorities": ["critical", "high"]}'
```

### Quick Scans

**Security scan**:

```bash
curl -X POST http://localhost:8004/api/v1/scan/security \
  -H "Content-Type: application/json" \
  -d '{
    "code": "eval(req.body.query)",
    "language": "javascript"
  }'
```

**Generate tests**:

```bash
curl -X POST http://localhost:8004/api/v1/generate/tests \
  -H "Content-Type: application/json" \
  -d '{
    "code": "function add(a, b) { return a + b; }",
    "language": "javascript",
    "test_framework": "jest"
  }'
```

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/review/submit` | Submit code for review |
| GET | `/api/v1/review/:id/status` | Check review status |
| GET | `/api/v1/review/:id/report` | Get review report |
| POST | `/api/v1/review/:id/fix` | Apply suggested fixes |
| DELETE | `/api/v1/review/:id` | Delete review session |
| POST | `/api/v1/scan/security` | Quick security scan |
| POST | `/api/v1/scan/performance` | Quick performance scan |
| POST | `/api/v1/generate/tests` | Generate test cases |
| GET | `/health` | Health check |

### MCP Tools

| Tool | Description |
|------|-------------|
| `submit_code_for_review` | Start comprehensive review |
| `get_review_status` | Check progress |
| `get_review_report` | Get detailed findings |
| `apply_fixes` | Auto-apply fixes |
| `quick_security_scan` | Fast security check |
| `generate_tests` | Create test cases |

## Council Agents

### QA Agent
- Generates comprehensive test cases
- Analyzes test coverage
- Identifies edge cases and error handling gaps
- Provides test recommendations

### Security Agent
- Scans for OWASP Top 10 vulnerabilities
- Detects SQL injection, XSS, auth bypass
- Checks for prompt injection (AI features)
- Identifies secret exposure
- Validates input handling

### Performance Agent
- Detects N+1 query problems
- Analyzes algorithm complexity
- Identifies memory leaks
- Finds blocking operations
- Suggests caching opportunities

### Architecture Agent
- Reviews design patterns
- Checks SOLID principles
- Analyzes code structure
- Measures maintainability
- Identifies code smells

### Chairman Agent
- Synthesizes all findings
- Calculates overall quality score
- Prioritizes issues
- Determines quality gate status
- Generates actionable recommendations

## Quality Gates

Reviews pass quality gates when:
- No critical issues
- No high-priority issues
- Overall score ≥ 70/100

## Testing

Run integration tests:

```bash
cd bridge
python test_bridge.py
```

Expected output:
```
✓ Health check passed
✓ Code submitted successfully
✓ Review completed
✓ Report retrieved
✓ Security scan passed
✓ Tests generated
✓ Fixes applied

Results: 7/7 tests passed
```

## Examples

See `examples/` directory for:
- `claude_example.md` - Claude Desktop integration
- `api_example.sh` - REST API usage
- `python_client.py` - Python client library
- `nodejs_client.js` - Node.js client library

## Configuration

### Environment Variables

**Bridge Service**:
- `PORT` - Bridge service port (default: 8004)
- `COUNCIL_URL` - Council service URL
- `SANDBOX_URL` - Sandbox service URL
- `REDIS_URL` - Redis connection URL

**Council Service**:
- `OPENROUTER_API_KEY` - OpenRouter API key (required)

**Sandbox Service**:
- `E2B_API_KEY` - E2B API key (required)

### Quality Gates

Customize which agents to run:

```json
{
  "quality_gates": ["qa", "security", "performance", "architecture"]
}
```

## Cost Estimate

**Per Review** (100 lines of code):
- LLM API calls: $0.05-0.15
- Sandbox execution: $0.01-0.05
- **Total: $0.06-0.20**

**Monthly** (100 reviews):
- LLM costs: $5-15
- E2B sandboxes: $2-5
- Infrastructure: $10-20
- **Total: $17-40/month**

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose -f docker-compose-bridge.yml logs

# Restart services
docker-compose -f docker-compose-bridge.yml restart
```

### Connection Errors

```bash
# Verify services are running
docker-compose -f docker-compose-bridge.yml ps

# Test each service
curl http://localhost:8001/health  # Council
curl http://localhost:8003/health  # Sandbox
curl http://localhost:8004/health  # Bridge
```

### MCP Not Working

1. Check Claude config path is correct
2. Verify absolute path to server.js
3. Restart Claude Desktop
4. Check Claude logs: `~/Library/Logs/Claude/`

### Slow Reviews

- Council agents take 30-60s to analyze
- Sandbox execution takes 30-120s
- Use quick scans for faster results

## Roadmap

- [ ] WebSocket streaming for real-time progress
- [ ] Multi-LLM adapters (Gemini, Qwen, GLM)
- [ ] ACP protocol support
- [ ] Caching layer for common reviews
- [ ] UI dashboard
- [ ] GitHub integration
- [ ] VS Code extension

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT

## Support

For issues and questions:
- GitHub Issues
- Documentation: `docs/`
- Examples: `examples/`

---

Built with ❤️ for better code quality
