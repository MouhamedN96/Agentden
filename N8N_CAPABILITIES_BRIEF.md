# n8n API Capabilities Brief

## Overview

The n8n API provides comprehensive programmatic access to manage workflows, executions, credentials, and automation resources. This brief outlines key capabilities relevant to the Code-on-Fly autonomous coding team system.

## Core Capabilities

### 1. Workflow Management

**List Workflows**
- `GET /api/v1/workflows`
- Retrieve all workflows in the instance
- Filter by active/inactive status
- Use case: Monitor available workflows, check deployment status

**Get Workflow Details**
- `GET /api/v1/workflows/{id}`
- Retrieve complete workflow definition including nodes and connections
- Use case: Inspect workflow configuration, debug issues

**Create Workflow**
- `POST /api/v1/workflows`
- Programmatically create new workflows
- Use case: Deploy Code-on-Fly orchestrator automatically

**Update Workflow**
- `PUT /api/v1/workflows/{id}`
- Modify existing workflow configuration
- Use case: Update service URLs, adjust parameters

**Activate/Deactivate Workflow**
- `PATCH /api/v1/workflows/{id}`
- Toggle workflow active state
- Use case: Enable/disable Code-on-Fly system

**Execute Workflow**
- `POST /api/v1/workflows/{id}/execute`
- Trigger workflow execution with custom data
- Use case: Programmatically start coding sessions

### 2. Execution Management

**List Executions**
- `GET /api/v1/executions`
- Retrieve execution history
- Filter by workflow, status, date range
- Use case: Monitor coding sessions, track success rate

**Get Execution Details**
- `GET /api/v1/executions/{id}`
- Retrieve complete execution data including node outputs
- Use case: Debug failed sessions, analyze performance

**Delete Execution**
- `DELETE /api/v1/executions/{id}`
- Clean up old execution data
- Use case: Manage storage, remove test data

### 3. Variable Management

**Create Variable**
- `POST /api/v1/variables`
- Store key-value pairs for workflow state
- Use case: Store project context, session data, council decisions

**List Variables**
- `GET /api/v1/variables`
- Retrieve all stored variables
- Use case: Access project state, retrieve session info

**Update Variable**
- `PATCH /api/v1/variables/{id}`
- Modify variable value
- Use case: Update project status, store progress

**Delete Variable**
- `DELETE /api/v1/variables/{id}`
- Remove variable
- Use case: Clean up completed projects

### 4. Credential Management

**List Credentials**
- `GET /api/v1/credentials`
- Retrieve all credentials (without sensitive data)
- Use case: Verify API keys are configured

**Create Credential**
- `POST /api/v1/credentials`
- Programmatically add credentials
- Use case: Automated setup, credential rotation

**Update Credential**
- `PUT /api/v1/credentials/{id}`
- Modify credential data
- Use case: Update API keys, rotate secrets

### 5. User Management

**List Users**
- `GET /api/v1/users`
- Retrieve all users (enterprise feature)
- Use case: Multi-tenant deployments

**Create User**
- `POST /api/v1/users`
- Add new users programmatically
- Use case: Automated onboarding

### 6. Tag Management

**List Tags**
- `GET /api/v1/tags`
- Retrieve all workflow tags
- Use case: Organize Code-on-Fly workflows

**Create Tag**
- `POST /api/v1/tags`
- Create new tags
- Use case: Categorize projects by type

### 7. Source Control

**Pull from Git**
- `POST /api/v1/source-control/pull`
- Pull workflow changes from git
- Use case: Sync workflow updates

**Push to Git**
- `POST /api/v1/source-control/push`
- Push workflow changes to git
- Use case: Version control for workflows

## Code-on-Fly Integration Points

### 1. Request Handling

**Capability**: Webhook nodes + Variable storage

**How it works**:
1. Slack sends request to n8n webhook
2. n8n parses request and creates project context
3. Stores context in n8n variables
4. Triggers council workflow

**API Usage**:
```python
# Store project context
requests.post(
    f"{N8N_BASE_URL}/api/v1/variables",
    headers={"X-N8N-API-KEY": api_key},
    json={
        "key": f"project_{project_id}",
        "value": json.dumps({
            "request": "build login feature",
            "status": "planning",
            "created_at": timestamp
        })
    }
)
```

### 2. Workflow Orchestration

**Capability**: HTTP Request nodes + Workflow execution

**How it works**:
1. n8n calls Council API for planning
2. Stores plan in variables
3. n8n calls Coder API for implementation
4. Monitors progress via webhooks
5. Calls Council API for review

**API Usage**:
```python
# Execute workflow programmatically
requests.post(
    f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}/execute",
    headers={"X-N8N-API-KEY": api_key},
    json={
        "data": {
            "project_id": project_id,
            "request": "build feature"
        }
    }
)
```

### 3. Progress Tracking

**Capability**: Webhook receivers + Execution monitoring

**How it works**:
1. Coder service sends progress to n8n webhook
2. n8n updates project variables
3. n8n sends Slack notifications
4. Execution history tracks all sessions

**API Usage**:
```python
# Monitor execution status
execution = requests.get(
    f"{N8N_BASE_URL}/api/v1/executions/{execution_id}",
    headers={"X-N8N-API-KEY": api_key}
).json()

print(f"Status: {execution['status']}")
print(f"Progress: {execution['data']['progress']}")
```

### 4. State Management

**Capability**: Variables API + Execution data

**How it works**:
1. Store project context in variables
2. Update status as workflow progresses
3. Retrieve context for review/deployment
4. Clean up after completion

**API Usage**:
```python
# Update project status
requests.patch(
    f"{N8N_BASE_URL}/api/v1/variables/{variable_id}",
    headers={"X-N8N-API-KEY": api_key},
    json={
        "value": json.dumps({
            "status": "implementing",
            "progress": 45,
            "session_id": session_id
        })
    }
)
```

### 5. Deployment Automation

**Capability**: Workflow execution + Source control

**How it works**:
1. Review complete, verdict is APPROVE
2. n8n triggers deployment workflow
3. Pushes code to git
4. Updates project status
5. Sends final notification

**API Usage**:
```python
# Trigger deployment workflow
requests.post(
    f"{N8N_BASE_URL}/api/v1/workflows/{deploy_workflow_id}/execute",
    headers={"X-N8N-API-KEY": api_key},
    json={
        "data": {
            "project_id": project_id,
            "git_repo": repo_url,
            "branch": "main"
        }
    }
)
```

## Advanced Features

### 1. Conditional Routing

**Use in Code-on-Fly**:
- Route to different workflows based on complexity
- Simple features → Fast track
- Complex features → Full council review

### 2. Error Handling

**Use in Code-on-Fly**:
- Retry failed API calls
- Fallback to alternative models
- Send error notifications to Slack

### 3. Parallel Execution

**Use in Code-on-Fly**:
- Council agents query in parallel
- Multiple features implemented simultaneously
- Concurrent code reviews

### 4. Scheduled Workflows

**Use in Code-on-Fly**:
- Daily summary of completed projects
- Weekly cost reports
- Monthly quality metrics

### 5. Sub-workflows

**Use in Code-on-Fly**:
- Modular workflow components
- Reusable council patterns
- Shared deployment logic

## Performance Considerations

### Rate Limits

- n8n Cloud: Varies by plan
- Self-hosted: No limits
- Recommendation: Batch operations when possible

### Execution Limits

- Cloud: Execution timeout varies by plan
- Self-hosted: Configurable
- Code-on-Fly: Long-running sessions need monitoring

### Storage

- Variables: Limited by plan
- Executions: Auto-cleanup recommended
- Code-on-Fly: Clean up completed projects

## Security Best Practices

### 1. API Key Management

- Use environment variables
- Rotate keys regularly
- Scope keys to minimum permissions (enterprise)

### 2. Webhook Security

- Use HTTPS only
- Validate webhook signatures (Slack)
- Implement rate limiting

### 3. Credential Storage

- Use n8n credential system
- Never store in variables
- Encrypt sensitive data

### 4. Access Control

- Limit API key access
- Use separate keys for dev/prod
- Monitor API usage

## Monitoring & Debugging

### 1. Execution Logs

```python
# Get execution with error details
execution = requests.get(
    f"{N8N_BASE_URL}/api/v1/executions/{execution_id}",
    headers={"X-N8N-API-KEY": api_key}
).json()

if execution['status'] == 'error':
    print(f"Error: {execution['data']['resultData']['error']}")
```

### 2. Workflow Metrics

```python
# Get all executions for a workflow
executions = requests.get(
    f"{N8N_BASE_URL}/api/v1/executions?workflowId={workflow_id}",
    headers={"X-N8N-API-KEY": api_key}
).json()

success_rate = sum(1 for e in executions if e['status'] == 'success') / len(executions)
print(f"Success rate: {success_rate * 100}%")
```

### 3. Performance Tracking

```python
# Calculate average execution time
total_time = sum(
    (datetime.fromisoformat(e['stoppedAt']) - datetime.fromisoformat(e['startedAt'])).seconds
    for e in executions if e['stoppedAt']
)
avg_time = total_time / len(executions)
print(f"Average execution time: {avg_time}s")
```

## Integration Patterns

### 1. Request-Response Pattern

```
User Request → n8n Webhook → Process → Respond
```

**Use case**: Simple feature requests

### 2. Long-Running Pattern

```
User Request → n8n Webhook → Start Background Process → Progress Webhooks → Complete
```

**Use case**: Code-on-Fly autonomous coding

### 3. Multi-Stage Pattern

```
Request → Stage 1 → Store State → Stage 2 → Store State → Stage 3 → Complete
```

**Use case**: Council planning → Coding → Review

### 4. Event-Driven Pattern

```
External Event → n8n Webhook → Process → Trigger Other Workflows
```

**Use case**: Git push → Deploy → Notify

## Cost Optimization

### 1. Execution Efficiency

- Minimize HTTP requests
- Use parallel execution
- Cache frequent queries

### 2. Storage Management

- Auto-delete old executions
- Clean up completed projects
- Compress large variables

### 3. API Usage

- Batch variable updates
- Use webhook triggers instead of polling
- Implement caching layer

## Conclusion

The n8n API provides all necessary capabilities for Code-on-Fly:

✅ **Workflow Orchestration** - Manage complex multi-stage processes
✅ **State Management** - Store and retrieve project context
✅ **Event Handling** - Webhooks for real-time updates
✅ **Execution Monitoring** - Track progress and debug issues
✅ **Integration** - Connect Council, Coder, and Slack seamlessly

**Key Strengths**:
- Visual workflow builder + API access
- Flexible state management with variables
- Robust webhook system
- Execution history and debugging
- Self-hosted or cloud options

**Recommended for**:
- Multi-agent orchestration
- Long-running autonomous processes
- Complex workflow automation
- Integration of multiple services

**Next Steps**:
1. Set up n8n instance
2. Import Code-on-Fly workflow
3. Configure API credentials
4. Test with simple feature request
5. Monitor and optimize
