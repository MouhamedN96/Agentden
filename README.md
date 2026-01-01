# AgentDen

Autonomous AI coding agent extension for Claude Code, Gemini CLI, Qwen Code, and other AI coding tools. Provides real-time code review, sandbox execution, and extensibility through MCPs, Skills, and Tools.

## What is AgentDen?

AgentDen is a bridge between your AI coding agent and a council of specialized agents that review, test, and validate code in real-time. It connects to your existing workflow without requiring context switching.

## Core Components

### 1. CLI Tool (`agentden`)

Command-line interface for code review and execution:

```bash
agentden review app.js              # Review code with council agents
agentden execute test.py            # Run code in sandbox
agentden config list                # View configuration
agentden config add-mcp github ...  # Add MCP server
```

### 2. Council Service

Multi-agent code review system with specialized agents:

- **QA Agent** - Code quality, best practices, design patterns
- **Security Agent** - OWASP Top 10, SQL injection, XSS, prompt injection
- **Performance Agent** - N+1 queries, memory leaks, optimization opportunities
- **Architecture Agent** - SOLID principles, design patterns, scalability

### 3. Sandbox Service

Isolated code execution environment using E2B:

- Execute code safely in sandboxed VMs
- Support for JavaScript, Python, Go, Rust, Java, C#, PHP
- Real-time output capture (stdout, stderr, exit code)
- Configurable timeout and resource limits

### 4. Bridge Service

Connects everything together:

- REST API for external tools
- MCP server for Claude Code
- WebSocket for real-time updates
- Plugin system for MCPs, Skills, Tools

## Quick Start

### Installation

```bash
npm install -g agentden-cli
```

### Initialize

```bash
agentden config init
```

### Review Code

```bash
agentden review app.js
```

Output:

```
Review Results for app.js
Quality Score: 87/100
Duration: 2341ms

HIGH (2)
──────────────────────────────────────────────────
[SECURITY] SQL Injection Vulnerability
  Line: 45
  Category: Security
  User input directly concatenated into SQL query
  Suggestion: Use parameterized queries
  ✓ Auto-fix available

MEDIUM (1)
──────────────────────────────────────────────────
[QA] Missing Error Handling
  Line: 23
  Category: Error Handling
  Promise rejection not handled
```

### Execute Code

```bash
agentden execute test.py
```

## Plugin System

### MCPs (Model Context Protocol)

Connect external services for enhanced analysis:

```bash
agentden config add-mcp github http://localhost:3000
agentden config add-mcp notion http://localhost:3001
```

Council agents can call MCPs during review to:
- Fetch repository context
- Check documentation
- Query databases
- Integrate with external tools

### Skills (Custom Functions)

Create custom analysis rules:

```bash
agentden config add-skill custom-lint ./skills/lint.js
```

Example skill:

```javascript
module.exports = {
  name: 'custom-lint',
  async execute(input) {
    const { code, language } = input
    // Your custom logic
    return { issues: [] }
  }
}
```

### Tools (External Integrations)

Configure ESLint, Prettier, and other tools:

```bash
agentden config add-tool eslint .eslintrc.json
agentden config add-tool prettier .prettierrc.json
```

## Integration with AI Coding Agents

### Claude Code (via MCP)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agentden": {
      "command": "agentden",
      "args": ["mcp"],
      "env": {
        "CLI_URL": "http://localhost:9000"
      }
    }
  }
}
```

Then in Claude Code:

```
Review this code for security issues:
[paste code]
```

Claude will automatically call AgentDen for analysis.

### Gemini CLI (via REST API)

```bash
curl -X POST http://localhost:9000/review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "...",
    "language": "javascript",
    "agents": ["security", "qa"]
  }'
```

### Qwen Code (via REST API)

Same REST API as Gemini CLI - any tool can integrate.

## Configuration

Configuration file: `~/.agentden/config.yaml`

```yaml
council:
  enabled: true
  agents:
    - qa
    - security
    - performance
    - architecture
  url: http://localhost:8001

sandbox:
  enabled: true
  provider: e2b
  timeout: 30
  url: http://localhost:8003

mcps:
  - name: github
    url: http://localhost:3000
    enabled: true

skills:
  - name: custom-lint
    path: ./skills/lint.js
    enabled: true

tools:
  - name: eslint
    config: .eslintrc.json
    enabled: true
```

## Services

AgentDen requires these services:

- **Council Service** (port 8001) - Code review with agents
- **Sandbox Service** (port 8003) - Code execution
- **Optional MCPs** - External services

See `council/` and `sandbox/` directories for service implementations.

## Architecture

```
Claude Code / Gemini CLI / Qwen Code
           ↓
    MCP Server / REST API
           ↓
    CLI Tool (agentden)
           ↓
    ┌──────────────────────────┐
    │  Council Review          │
    │  Sandbox Execution       │
    │  Plugin System           │
    └──────────────────────────┘
           ↓
    ┌──────────────────────────┐
    │  MCPs                    │
    │  Skills                  │
    │  Tools                   │
    └──────────────────────────┘
```

## Project Structure

```
agentden/
├── cli/                    # CLI tool
│   ├── src/
│   │   ├── cli/           # Commands
│   │   ├── council/       # Council client
│   │   ├── sandbox/       # Sandbox client
│   │   ├── plugins/       # Plugin system
│   │   ├── config/        # Configuration
│   │   └── mcp/           # Claude Code MCP
│   ├── examples/          # Configuration & skills
│   └── README.md
├── council/                # Council service
│   ├── main.py
│   ├── main_multi_llm.py
│   └── Dockerfile
├── coder/                  # Autonomous coder
│   ├── main.py
│   └── main_with_sandbox.py
├── sandbox/                # Sandbox service
│   └── main.py
├── bridge/                 # Bridge service
│   ├── api/
│   ├── mcp/
│   └── lib/
├── n8n-workflows/          # n8n orchestration
├── docs/                   # Documentation
└── README.md
```

## Multi-LLM Support

AgentDen supports multiple LLM providers:

- **Groq** - Ultra-fast, ultra-cheap (recommended for production)
- **Ollama** - Free, local, private (recommended for development)
- **OpenRouter** - Access 100+ models
- **Anthropic** - Claude (highest quality)
- **OpenAI** - GPT-4

Configure in `council/config.py`:

```python
LLM_PROVIDERS = {
    'groq': {
        'model': 'llama-3.1-70b-versatile',
        'api_key': os.getenv('GROQ_API_KEY'),
    },
    'ollama': {
        'model': 'llama2',
        'base_url': 'http://localhost:11434',
    },
}
```

## Getting Started

1. **Install CLI**: `npm install -g agentden-cli`
2. **Initialize**: `agentden config init`
3. **Start services**: Run council and sandbox services
4. **Review code**: `agentden review app.js`
5. **Integrate**: Add MCP to Claude Code or use REST API

## Documentation

- `cli/README.md` - CLI tool documentation
- `docs/CLI_ARCHITECTURE.md` - Architecture and design
- `council/` - Council service implementation
- `sandbox/` - Sandbox service implementation
- `bridge/` - Bridge service implementation

## License

MIT
