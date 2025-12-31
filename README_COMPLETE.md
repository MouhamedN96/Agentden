# Code-on-Fly: Autonomous AI Coding Team
## With Multi-LLM Support (Groq, OpenRouter, Ollama)

Build features on demand with an AI coding team that plans, codes, tests, and deploys automatically.

---

## What It Does

Request a feature via Slack, and watch your AI team:

1. **Plan** - Council agents debate the best approach
2. **Code** - Autonomous coder implements the feature
3. **Test** - Sandbox VMs execute real tests
4. **Review** - Quality agents scrutinize security, performance, QA
5. **Deploy** - Code is committed and deployed automatically

All orchestrated by n8n, powered by multiple LLM providers for cost and speed.

---

## Architecture

```
Slack Request
    ↓
n8n Orchestrator
    ↓
Council Agents (QA, Security, Performance, Architecture)
    ↓
Autonomous Coder
    ↓
Sandbox VMs (Test, Security, Performance)
    ↓
Quality Review
    ↓
Git Commit + Deploy
    ↓
Slack Notification
```

**Multi-LLM Support**:
- **Groq**: Ultra-fast, ultra-cheap (primary)
- **Ollama**: Free, local, private (development)
- **OpenRouter**: Access all models (fallback)
- **Claude/GPT-4**: High quality (optional)

---

## Why Multi-LLM?

### Cost Comparison (1000 reviews)

| Provider | Cost | vs Claude |
|----------|------|-----------|
| **Groq** | **$0.10** | **99.5% cheaper** |
| **Ollama** | **FREE** | **100% cheaper** |
| OpenRouter | $4.50 | 78% cheaper |
| Claude | $21.00 | Baseline |

### Speed Comparison

| Provider | Tokens/sec | Review Time |
|----------|------------|-------------|
| **Groq** | **500+** | **2-3s** |
| Ollama | 50-100 | 5-10s |
| OpenRouter | 100-200 | 5-8s |
| Claude | 50-80 | 8-12s |

**Result**: Groq is 3-5x faster and 200x cheaper!

---

## Quick Start

### 1. Get API Keys (5 minutes)

**Groq** (Recommended - ultra-fast, ultra-cheap):
- Get key: https://console.groq.com
- Free tier: 30 requests/minute
- Cost: $0.05 per 1M input tokens

**OpenRouter** (Optional - access all models):
- Get key: https://openrouter.ai
- Free models available
- Pay-as-you-go pricing

**Ollama** (Optional - free, local):
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:70b
ollama serve
```

**E2B** (For sandboxes):
- Get key: https://e2b.dev
- Free tier: 100 hours/month

### 2. Configure Environment

```bash
cd code-on-fly

# Create .env
cat > .env << EOF
# Primary LLM (choose one or multiple)
GROQ_API_KEY=gsk_your_key_here
OPENROUTER_API_KEY=sk_or_your_key_here
OLLAMA_BASE_URL=http://localhost:11434/v1

# Sandbox
E2B_API_KEY=your_e2b_key_here

# n8n (optional)
N8N_INSTANCE_URL=https://your-n8n.app.n8n.cloud
N8N_API_KEY=your_n8n_key_here

# Slack (optional)
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret
EOF
```

### 3. Start Services

```bash
# Start all services
docker-compose -f docker-compose-bridge.yml up -d

# Verify
curl http://localhost:8004/health
curl http://localhost:8001/providers
```

### 4. Test It

```bash
cd bridge
python test_bridge.py
```

Expected: All tests pass! ✅

---

## Components

### 1. Bridge Service (Port 8004)
- REST API for code review
- WebSocket for real-time updates
- MCP server for Claude Desktop
- Session management

### 2. Council Service (Port 8001)
- **QA Agent**: Test generation, coverage analysis
- **Security Agent**: OWASP, SQL injection, XSS, prompt injection
- **Performance Agent**: N+1 queries, algorithm complexity, memory leaks
- **Architecture Agent**: Design patterns, SOLID principles, code smells
- **Chairman Agent**: Synthesizes findings, calculates scores

### 3. Sandbox Service (Port 8003)
- Test VM: Run unit/integration tests
- Security VM: Pen-testing, vulnerability scanning
- Performance VM: Benchmarks, load testing

### 4. n8n Orchestrator (Optional)
- Slack integration
- Workflow management
- Progress tracking
- Deployment automation

---

## Usage

### Via Claude Desktop (MCP)

1. Configure Claude Desktop:
```json
{
  "mcpServers": {
    "code-quality-bridge": {
      "command": "node",
      "args": ["/path/to/code-on-fly/bridge/mcp/server.js"],
      "env": {
        "BRIDGE_URL": "http://localhost:8004"
      }
    }
  }
}
```

2. In Claude Desktop:
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

Claude will automatically review and suggest fixes!

### Via REST API

```bash
# Submit code
curl -X POST http://localhost:8004/api/v1/review/submit \
  -H "Content-Type: application/json" \
  -d '{
    "code": "...",
    "language": "javascript",
    "quality_gates": ["security", "qa"],
    "llm_preference": "fast"
  }'

# Get report
curl http://localhost:8004/api/v1/review/{session_id}/report

# Apply fixes
curl -X POST http://localhost:8004/api/v1/review/{session_id}/fix
```

### Via Slack (with n8n)

```
/code-team build user authentication with JWT
```

n8n orchestrates the entire workflow automatically!

---

## LLM Provider Selection

### Automatic (Recommended)

System automatically selects the best provider for each task:

- **Fast tasks** (security scans): Groq
- **Cheap tasks** (development): Ollama
- **Quality tasks** (architecture): Claude via OpenRouter
- **Balanced tasks** (general reviews): Groq

### Manual

Specify preference in API requests:

```json
{
  "llm_preference": "fast"  // or "cheap", "quality", "balanced"
}
```

---

## Cost Analysis

### Development (Ollama)

- **Cost**: FREE
- **Speed**: 50-100 tokens/sec
- **Setup**: 5 minutes
- **Privacy**: Code never leaves your machine

### Production (Groq)

**Per Review**:
- LLM: $0.0001
- Sandbox: $0.01
- **Total**: $0.0101

**Monthly** (100 reviews):
- LLM: $0.01
- Sandbox: $1.00
- Infrastructure: $10-20
- **Total**: $11-21/month

**Annual** (1000 reviews):
- **Total**: $110-210/year

**Savings vs Claude**: $2,500/year (95% reduction!)

---

## Features

### Code Review
- ✅ Security vulnerability detection
- ✅ OWASP Top 10 scanning
- ✅ SQL injection, XSS, auth bypass
- ✅ Prompt injection (AI features)
- ✅ Secret exposure detection

### Quality Assurance
- ✅ Test generation (unit, integration, edge cases)
- ✅ Coverage analysis
- ✅ Error handling validation
- ✅ Edge case identification

### Performance
- ✅ N+1 query detection
- ✅ Algorithm complexity analysis
- ✅ Memory leak detection
- ✅ Blocking operation identification
- ✅ Caching opportunity suggestions

### Architecture
- ✅ Design pattern validation
- ✅ SOLID principles checking
- ✅ Code smell detection
- ✅ Maintainability metrics
- ✅ Coupling/cohesion analysis

### Automation
- ✅ Automatic fix application
- ✅ Quality gate enforcement
- ✅ Real-time progress updates
- ✅ Slack notifications
- ✅ Git integration

---

## Documentation

- **Quick Start**: `BRIDGE_QUICKSTART.md`
- **Multi-LLM Setup**: `docs/MULTI_LLM_SETUP.md`
- **Bridge API**: `bridge/README.md`
- **Claude Integration**: `bridge/examples/claude_example.md`
- **Architecture**: `docs/BRIDGE_ARCHITECTURE.md`
- **Implementation Plan**: `docs/BRIDGE_IMPLEMENTATION_PLAN.md`

---

## Examples

### Example 1: Security Review

**Input**:
```javascript
function login(username, password) {
    const user = db.query(`SELECT * FROM users WHERE username='${username}'`);
    if (user && user.password === password) {
        return { token: generateToken(user) };
    }
    return null;
}
```

**Output**:
```
🚨 CRITICAL ISSUES FOUND

1. SQL Injection (Line 2)
   - Exploit: ' OR '1'='1
   - Fix: Use parameterized queries

2. Plain Text Password (Line 3)
   - Exploit: Password comparison in plain text
   - Fix: Use bcrypt hashing

Overall Score: 25/100
Quality Gate: FAILED ❌
```

### Example 2: Test Generation

**Input**:
```javascript
function calculateDiscount(price, discountPercent) {
    return price * (1 - discountPercent / 100);
}
```

**Output**:
```javascript
describe('calculateDiscount', () => {
    test('applies 10% discount correctly', () => {
        expect(calculateDiscount(100, 10)).toBe(90);
    });
    
    test('handles 0% discount', () => {
        expect(calculateDiscount(100, 0)).toBe(100);
    });
    
    test('handles 100% discount', () => {
        expect(calculateDiscount(100, 100)).toBe(0);
    });
    
    // ... 7 more tests covering edge cases
});

Coverage: 100% functions, 100% lines, 100% branches
```

---

## Deployment

### Local Development

```bash
# Use Ollama (free)
ollama serve
docker-compose up -d
```

### Production

```bash
# Use Groq (cheap, fast)
export GROQ_API_KEY=...
docker-compose -f docker-compose-bridge.yml up -d
```

### High Availability

```bash
# Multiple providers
export GROQ_API_KEY=...
export OPENROUTER_API_KEY=...
export OLLAMA_BASE_URL=...
docker-compose up -d
```

---

## Roadmap

- [x] Bridge Service with REST API
- [x] MCP Server for Claude Desktop
- [x] Multi-LLM support (Groq, OpenRouter, Ollama)
- [x] Council agents (QA, Security, Performance, Architecture)
- [x] Sandbox VM integration
- [x] Comprehensive documentation
- [ ] WebSocket streaming
- [ ] GitHub integration
- [ ] VS Code extension
- [ ] UI dashboard
- [ ] CI/CD integration
- [ ] Team collaboration features

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests
4. Submit a pull request

---

## License

MIT

---

## Support

- **Documentation**: See `docs/` directory
- **Examples**: See `bridge/examples/`
- **Issues**: Open a GitHub issue
- **Discussions**: GitHub Discussions

---

## Acknowledgments

Built with:
- **Groq**: Ultra-fast LLM inference
- **Ollama**: Local LLM hosting
- **OpenRouter**: Multi-model access
- **E2B**: Secure sandboxes
- **n8n**: Workflow automation
- **FastAPI**: Python web framework
- **Express.js**: Node.js web framework

---

**Built with ❤️ for better, faster, cheaper code quality**

🚀 **Get started in 10 minutes**
💰 **Save 95% on LLM costs**
⚡ **Get reviews 5x faster**
🔒 **Catch vulnerabilities automatically**
✅ **Ship with confidence**
