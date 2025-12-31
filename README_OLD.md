# Code-on-Fly 🚀

> **Autonomous AI Coding Team** - Request features via Slack, let AI agents debate, plan, implement, and deploy code automatically.

## What is Code-on-Fly?

Code-on-Fly is an autonomous multi-agent coding system that combines:

- **LLM Council** (inspired by [karpathy/llm-council](https://github.com/karpathy/llm-council)) - Multiple AI agents collaborate to plan features
- **Autonomous Coder** (inspired by [leonvanzyl/autonomous-coding](https://github.com/leonvanzyl/autonomous-coding)) - AI agent implements features autonomously
- **n8n Orchestration** - Workflow automation connecting all components
- **Slack Interface** - Natural language feature requests
- **OpenRouter** - Single API for multiple LLM models

## How It Works

```
You in Slack: "/code-team build user authentication with JWT"
                    ↓
            n8n receives request
                    ↓
        LLM Council debates approach
        (4 specialist AI agents)
                    ↓
        Chairman synthesizes plan
                    ↓
        Autonomous Coder implements
        (writes code, runs tests, commits)
                    ↓
        LLM Council reviews code
                    ↓
        Deploy & notify you in Slack
```

## Key Features

✅ **Multi-Agent Planning** - 4 specialized AI agents (Architect, Security, Performance, Testing) debate the best approach

✅ **Autonomous Implementation** - AI writes code, runs tests, and commits to git automatically

✅ **Code Review** - Council reviews code quality, security, and performance before deployment

✅ **Real-Time Updates** - Progress updates sent to Slack as features are completed

✅ **n8n Orchestration** - Visual workflow automation connecting all components

✅ **Cost-Effective** - Uses OpenRouter to access multiple models with a single API key

## Architecture

```
┌─────────────┐
│   Slack     │ User requests feature
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│  n8n Orchestrator    │ Manages workflow
└──────┬───────────┬───┘
       │           │
       ▼           ▼
┌──────────┐  ┌──────────┐
│ Council  │  │  Coder   │
│ Service  │◄─┤ Service  │
└────┬─────┘  └────┬─────┘
     │             │
     ▼             ▼
┌──────────┐  ┌──────────┐
│OpenRouter│  │   Git    │
└──────────┘  └──────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- n8n instance (cloud or self-hosted)
- OpenRouter API key
- Anthropic API key
- Slack workspace

### 1. Clone and Configure

```bash
git clone <your-repo>
cd code-on-fly

# Create .env file
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Import n8n Workflow

1. Log into n8n
2. Import `n8n-workflows/code-on-fly-orchestrator.json`
3. Configure Slack credentials
4. Activate workflow

### 4. Configure Slack

1. Create Slack app at https://api.slack.com/apps
2. Add slash command `/code-team`
3. Point to your n8n webhook URL
4. Install app to workspace

### 5. Test It!

In Slack:
```
/code-team build a REST API endpoint for user registration
```

Watch as the AI team:
1. Debates the approach
2. Creates implementation plan
3. Writes the code
4. Runs tests
5. Reviews quality
6. Deploys and notifies you

## Council Agents

The LLM Council consists of 4 specialized agents:

| Agent | Model | Focus |
|-------|-------|-------|
| **Architect** | Claude Sonnet 4.5 | System design, patterns, scalability |
| **Security** | GPT-4.1 Mini | Auth, vulnerabilities, data protection |
| **Performance** | Gemini 2.5 Flash | Optimization, caching, queries |
| **Testing** | Grok 4 | Test strategy, coverage, edge cases |
| **Chairman** | Claude Sonnet 4.5 | Synthesizes final decision |

## Project Structure

```
code-on-fly/
├── council/              # LLM Council service
│   ├── main.py          # FastAPI service
│   ├── Dockerfile
│   └── requirements.txt
├── coder/               # Autonomous Coder service
│   ├── main.py          # FastAPI service
│   ├── Dockerfile
│   └── requirements.txt
├── n8n-workflows/       # n8n workflow definitions
│   └── code-on-fly-orchestrator.json
├── docs/                # Documentation
│   └── architecture.md
├── examples/            # Example requests and outputs
├── docker-compose.yml   # Service orchestration
├── .env.example         # Environment template
└── README.md           # This file
```

## API Endpoints

### Council Service (Port 8001)

**POST /council/plan**
```json
{
  "request": "build user authentication",
  "context": {}
}
```

**POST /council/review**
```json
{
  "code": "...",
  "tests": "...",
  "original_plan": {}
}
```

### Coder Service (Port 8002)

**POST /code/implement**
```json
{
  "plan": {},
  "project_dir": "project-123",
  "webhook_url": "https://n8n.../webhook/progress",
  "max_iterations": 50
}
```

**GET /code/status/{session_id}**

Returns current implementation progress.

## Configuration

### Environment Variables

```bash
# OpenRouter (for Council)
OPENROUTER_API_KEY=sk-or-v1-...

# Anthropic (for Coder)
ANTHROPIC_API_KEY=sk-ant-...

# n8n
N8N_INSTANCE_URL=https://your-instance.app.n8n.cloud
N8N_API_KEY=...

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...

# GitHub (optional)
GITHUB_TOKEN=ghp_...
GITHUB_ORG=your-org
```

### Customizing Council Models

Edit `council/main.py`:

```python
COUNCIL_ROLES = {
    "architect": {
        "model": "anthropic/claude-sonnet-4.5",
        "role": "System Architect",
        "focus": "Your custom focus"
    },
    # Add more agents...
}
```

## Cost Estimates

Based on OpenRouter pricing (as of Dec 2024):

| Task | Tokens | Cost |
|------|--------|------|
| Planning (4 agents) | ~20K | $0.06 |
| Code Review (4 agents) | ~15K | $0.045 |
| Implementation | Varies | Anthropic pricing |

**Typical feature cost: $0.20 - $2.00** depending on complexity.

## Monitoring

### Service Health

```bash
# Check all services
docker-compose ps

# Check logs
docker-compose logs -f

# Test endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
```

### n8n Executions

1. Go to n8n Executions tab
2. View real-time workflow progress
3. Debug any failures

### Session Status

```bash
# Get session ID from n8n execution
curl http://localhost:8002/code/status/session-123456
```

## Production Deployment

See [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) for detailed production deployment instructions including:

- Cloud deployment (AWS, GCP, DigitalOcean)
- Security best practices
- Monitoring and alerting
- Cost optimization
- Scaling strategies

## Troubleshooting

### Services won't start
```bash
docker-compose logs
docker-compose restart
```

### Webhook not working
- Check n8n webhook URL is correct
- Verify webhook is activated in n8n
- Test with curl

### Council not responding
- Verify OpenRouter API key
- Check model names are correct
- Review service logs

### Coder session stuck
- Check session status endpoint
- Review coder logs
- Restart coder service

## Examples

### Example 1: Simple API Endpoint

**Request:**
```
/code-team build a GET /health endpoint that returns status and timestamp
```

**Output:**
- Planning: 30 seconds
- Implementation: 2 minutes
- Review: 20 seconds
- Total: ~3 minutes

### Example 2: Authentication System

**Request:**
```
/code-team implement JWT authentication with login, logout, and token refresh
```

**Output:**
- Planning: 1 minute
- Implementation: 15 minutes
- Review: 1 minute
- Total: ~17 minutes

### Example 3: Database Integration

**Request:**
```
/code-team add PostgreSQL database with user model and CRUD operations
```

**Output:**
- Planning: 1.5 minutes
- Implementation: 20 minutes
- Review: 1.5 minutes
- Total: ~23 minutes

## Roadmap

- [ ] Multi-language support (Python, Go, Rust)
- [ ] Visual dashboard for monitoring
- [ ] Human-in-the-loop approval gates
- [ ] Learning system (improve from past projects)
- [ ] Cost predictor
- [ ] Integration marketplace
- [ ] Team collaboration (multiple users)
- [ ] Automatic PR creation

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [karpathy/llm-council](https://github.com/karpathy/llm-council) - Multi-LLM collaboration pattern
- [leonvanzyl/autonomous-coding](https://github.com/leonvanzyl/autonomous-coding) - Autonomous coding implementation
- [n8n](https://n8n.io/) - Workflow automation platform
- [OpenRouter](https://openrouter.ai/) - Multi-LLM API access
- [Anthropic](https://anthropic.com/) - Claude AI models

## Support

For questions and issues:
- Review [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)
- Check service logs
- Test components individually
- Open an issue on GitHub

---

**Built with ❤️ for developers who want AI teammates, not just tools.**
