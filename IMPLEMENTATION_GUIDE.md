# Code-on-Fly Implementation Guide

## Quick Start

This guide will help you set up and deploy your autonomous coding team system.

## Prerequisites

- Docker and Docker Compose
- n8n instance (cloud or self-hosted)
- OpenRouter API key
- Anthropic API key (for Claude)
- Slack workspace with admin access
- GitHub account (for code storage)

## Step 1: Environment Setup

### 1.1 Clone and Configure

```bash
# Create project directory
mkdir code-on-fly && cd code-on-fly

# Create environment file
cat > .env << EOF
# OpenRouter (for LLM Council)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Anthropic (for Autonomous Coder)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# n8n Configuration
N8N_INSTANCE_URL=https://your-instance.app.n8n.cloud
N8N_API_KEY=your-n8n-api-key

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# GitHub (for code storage)
GITHUB_TOKEN=ghp_your-token
GITHUB_ORG=your-organization

# Service URLs (for local development)
COUNCIL_URL=http://localhost:8001
CODER_URL=http://localhost:8002
N8N_WEBHOOK_BASE=https://your-instance.app.n8n.cloud/webhook
EOF
```

### 1.2 Get API Keys

**OpenRouter:**
1. Go to https://openrouter.ai/
2. Sign up and add credits
3. Create API key in Settings

**Anthropic:**
1. Go to https://console.anthropic.com/
2. Create account and add payment method
3. Generate API key

**n8n:**
1. Log into your n8n instance
2. Go to Settings > n8n API
3. Create API key

**Slack:**
1. Go to https://api.slack.com/apps
2. Create new app
3. Add Bot Token Scopes: `chat:write`, `commands`, `channels:read`
4. Install app to workspace
5. Copy Bot Token and Signing Secret

## Step 2: Deploy Services

### 2.1 Create Docker Compose File

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  council:
    build: ./council
    container_name: llm-council
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    ports:
      - "8001:8001"
    restart: unless-stopped
    networks:
      - code-on-fly

  coder:
    build: ./coder
    container_name: autonomous-coder
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - N8N_WEBHOOK_URL=${N8N_WEBHOOK_BASE}/progress
    volumes:
      - ./projects:/projects
      - ./coder/security.py:/app/security.py
    ports:
      - "8002:8002"
    restart: unless-stopped
    networks:
      - code-on-fly

  redis:
    image: redis:7-alpine
    container_name: code-on-fly-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - code-on-fly

networks:
  code-on-fly:
    driver: bridge

volumes:
  projects:
EOF
```

### 2.2 Create Dockerfiles

**Council Service:**
```bash
cat > council/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8001

CMD ["python", "main.py"]
EOF

cat > council/requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
pydantic==2.5.3
python-dotenv==1.0.0
EOF
```

**Coder Service:**
```bash
cat > coder/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install git and other dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8002

CMD ["python", "main.py"]
EOF

cat > coder/requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
pydantic==2.5.3
python-dotenv==1.0.0
EOF
```

### 2.3 Start Services

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify services are running
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## Step 3: Configure n8n Workflows

### 3.1 Import Workflow

1. Log into your n8n instance
2. Click "Add workflow" → "Import from File"
3. Upload `n8n-workflows/code-on-fly-orchestrator.json`
4. Activate the workflow

### 3.2 Configure Webhook URLs

The workflow contains two webhooks:

1. **Slack Request Webhook**: `/webhook/code-request`
   - Full URL: `https://your-instance.app.n8n.cloud/webhook/code-request`
   - Use this for Slack slash command

2. **Progress Webhook**: `/webhook/progress`
   - Full URL: `https://your-instance.app.n8n.cloud/webhook/progress`
   - Used internally by the coder service

### 3.3 Update Service URLs in Workflow

In the n8n workflow, update these HTTP Request nodes:

- **LLM Council - Plan**: Change URL to your council service
  - Local: `http://host.docker.internal:8001/council/plan`
  - Production: `https://your-council-service.com/council/plan`

- **Start Autonomous Coder**: Change URL to your coder service
  - Local: `http://host.docker.internal:8002/code/implement`
  - Production: `https://your-coder-service.com/code/implement`

## Step 4: Configure Slack

### 4.1 Create Slash Command

1. Go to your Slack app settings
2. Navigate to "Slash Commands"
3. Click "Create New Command"
4. Configure:
   - Command: `/code-team`
   - Request URL: `https://your-instance.app.n8n.cloud/webhook/code-request`
   - Short Description: "Request feature from AI coding team"
   - Usage Hint: `[feature description]`
5. Save

### 4.2 Add Slack Credentials to n8n

1. In n8n, go to Credentials
2. Add new "Slack" credential
3. Enter your Bot Token
4. Test connection
5. Use this credential in all Slack nodes in the workflow

## Step 5: Test the System

### 5.1 Simple Test

In Slack, type:
```
/code-team build a simple hello world API endpoint
```

You should see:
1. Acknowledgment message
2. Planning complete message
3. Progress updates as features are implemented
4. Final deployment message with quality scores

### 5.2 Monitor Execution

**n8n:**
- Go to Executions tab
- Watch the workflow execute in real-time
- Check for any errors

**Service Logs:**
```bash
# Council logs
docker logs -f llm-council

# Coder logs
docker logs -f autonomous-coder
```

**Check Session Status:**
```bash
# Get session ID from n8n execution
SESSION_ID="session-123456"

# Check status
curl http://localhost:8002/code/status/$SESSION_ID
```

## Step 6: Production Deployment

### 6.1 Deploy to Cloud

**Option 1: AWS ECS**
```bash
# Build and push images
docker build -t your-registry/council:latest ./council
docker push your-registry/council:latest

docker build -t your-registry/coder:latest ./coder
docker push your-registry/coder:latest

# Deploy using ECS task definitions
# (See AWS documentation)
```

**Option 2: Google Cloud Run**
```bash
# Build and deploy council
gcloud builds submit --tag gcr.io/your-project/council ./council
gcloud run deploy council --image gcr.io/your-project/council

# Build and deploy coder
gcloud builds submit --tag gcr.io/your-project/coder ./coder
gcloud run deploy coder --image gcr.io/your-project/coder
```

**Option 3: DigitalOcean App Platform**
```bash
# Use App Platform UI to deploy from GitHub
# Point to council/ and coder/ directories
# Set environment variables in UI
```

### 6.2 Configure Production URLs

Update your `.env` file with production URLs:
```bash
COUNCIL_URL=https://council.your-domain.com
CODER_URL=https://coder.your-domain.com
```

Update n8n workflow HTTP Request nodes with production URLs.

### 6.3 Set Up Monitoring

**Uptime Monitoring:**
```bash
# Add health check endpoints to monitoring service
https://council.your-domain.com/health
https://coder.your-domain.com/health
```

**Log Aggregation:**
- Use CloudWatch (AWS), Cloud Logging (GCP), or Papertrail
- Configure log shipping from containers

**Alerts:**
- Set up alerts for service downtime
- Alert on high error rates
- Alert on long-running sessions

## Step 7: Advanced Configuration

### 7.1 Customize Council Models

Edit `council/main.py`:
```python
COUNCIL_ROLES = {
    "architect": {
        "model": "anthropic/claude-sonnet-4.5",  # Change model
        "role": "System Architect",
        "focus": "Your custom focus areas"
    },
    # Add more roles...
}
```

### 7.2 Add Security Sandbox

For production, integrate the security sandbox from autonomous-coding:

```bash
# Copy security.py from autonomous-coding repo
cp ../autonomous-coding/security.py coder/

# Update coder/main.py to use security hooks
# (See autonomous-coding implementation)
```

### 7.3 Enable Git Integration

Update coder service to push to GitHub:

```python
# In coder/main.py, after implementation complete:
os.system(f"""
cd {project_dir} && \
git remote add origin https://{GITHUB_TOKEN}@github.com/{GITHUB_ORG}/{project_name}.git && \
git push -u origin main
""")
```

### 7.4 Add Human-in-the-Loop

Add approval step in n8n workflow:

1. After "LLM Council - Plan" node
2. Add "Wait for Webhook" node
3. Send Slack message with approval buttons
4. Wait for user approval before starting coder

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Verify environment variables
docker-compose config

# Restart services
docker-compose restart
```

### Webhook Not Receiving Data

```bash
# Test webhook directly
curl -X POST https://your-instance.app.n8n.cloud/webhook/code-request \
  -H "Content-Type: application/json" \
  -d '{"text": "test feature", "user_id": "U123", "channel_id": "C123"}'

# Check n8n execution logs
# Verify webhook is activated
```

### Council Not Responding

```bash
# Test council directly
curl -X POST http://localhost:8001/council/plan \
  -H "Content-Type: application/json" \
  -d '{"request": "build login", "context": {}}'

# Check OpenRouter API key
# Verify model names are correct
```

### Coder Session Stuck

```bash
# Check session status
curl http://localhost:8002/code/status/session-123456

# Check coder logs
docker logs autonomous-coder

# Restart coder service
docker-compose restart coder
```

## Cost Optimization

### Model Selection

**Expensive but High Quality:**
- `anthropic/claude-sonnet-4.5` - $3/M tokens
- Use for: Chairman, Architect, Final Review

**Balanced:**
- `openai/gpt-4.1-mini` - $0.15/M tokens
- Use for: Security, Testing

**Cheap and Fast:**
- `google/gemini-2.5-flash` - $0.075/M tokens
- Use for: Performance analysis, Simple tasks

### Caching

Implement response caching for similar requests:

```python
# In council/main.py
import hashlib
import redis

redis_client = redis.Redis(host='redis', port=6379)

def get_cached_plan(request: str):
    cache_key = hashlib.md5(request.encode()).hexdigest()
    cached = redis_client.get(f"plan:{cache_key}")
    if cached:
        return json.loads(cached)
    return None

def cache_plan(request: str, plan: dict):
    cache_key = hashlib.md5(request.encode()).hexdigest()
    redis_client.setex(f"plan:{cache_key}", 3600, json.dumps(plan))
```

### Batch Progress Updates

Instead of sending webhook for every feature, batch updates:

```python
# Only send webhook every 5 features or 10% progress
if passing % 5 == 0 or (passing / total) % 0.1 < 0.01:
    await send_progress_webhook(webhook_url, payload)
```

## Security Best Practices

1. **API Keys**: Use secrets manager (AWS Secrets Manager, GCP Secret Manager)
2. **Network**: Use VPC and private subnets for services
3. **Authentication**: Add API key authentication to council/coder services
4. **Rate Limiting**: Implement rate limiting on all endpoints
5. **Input Validation**: Validate all user inputs before processing
6. **Sandbox**: Use the security sandbox from autonomous-coding for code execution
7. **Audit Logs**: Log all requests and decisions for audit trail

## Next Steps

1. **Add More Agents**: Create specialized agents for frontend, backend, DevOps
2. **Visual Dashboard**: Build React dashboard to monitor coding team activity
3. **Metrics**: Track success rate, cost per feature, time to deployment
4. **Learning**: Store successful patterns and reuse them
5. **Integration**: Add integrations with Jira, Linear, GitHub Issues
6. **Multi-Language**: Extend beyond Node.js to Python, Go, Rust
7. **Testing**: Add automated testing before deployment
8. **CI/CD**: Integrate with GitHub Actions or GitLab CI

## Support

For issues and questions:
- Check logs first: `docker-compose logs`
- Review n8n execution history
- Test services individually
- Check API key validity
- Verify network connectivity

## Resources

- [n8n Documentation](https://docs.n8n.io/)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Anthropic Claude Documentation](https://docs.anthropic.com/)
- [Slack API Documentation](https://api.slack.com/)
- [Autonomous Coding Repo](https://github.com/leonvanzyl/autonomous-coding)
- [LLM Council Repo](https://github.com/karpathy/llm-council)
