/**
 * Bridge Service - Code Quality Bridge API
 * Connects AI coding assistants with Council agents
 */

import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import Redis from 'ioredis';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Configuration
const PORT = process.env.PORT || 8004;
const COUNCIL_URL = process.env.COUNCIL_URL || 'http://localhost:8001';
const SANDBOX_URL = process.env.SANDBOX_URL || 'http://localhost:8003';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

// Initialize Express
const app = express();
const httpServer = createServer(app);

// Initialize Socket.IO
const io = new SocketIOServer(httpServer, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// Initialize Redis
const redis = new Redis(REDIS_URL);

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Request logging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
  next();
});

// Session storage helpers
async function saveSession(session) {
  await redis.set(
    `session:${session.id}`,
    JSON.stringify(session),
    'EX',
    3600 // 1 hour expiry
  );
}

async function getSession(sessionId) {
  const data = await redis.get(`session:${sessionId}`);
  return data ? JSON.parse(data) : null;
}

async function updateSession(sessionId, updates) {
  const session = await getSession(sessionId);
  if (!session) throw new Error('Session not found');
  
  const updated = { ...session, ...updates, updated_at: new Date().toISOString() };
  await saveSession(updated);
  return updated;
}

// Council API helpers
async function callCouncil(endpoint, data) {
  try {
    const response = await axios.post(`${COUNCIL_URL}${endpoint}`, data, {
      timeout: 120000 // 2 minutes
    });
    return response.data;
  } catch (error) {
    console.error(`Council API error: ${error.message}`);
    throw new Error(`Council service error: ${error.response?.data?.detail || error.message}`);
  }
}

async function callSandbox(endpoint, method = 'POST', data = null) {
  try {
    const config = {
      method,
      url: `${SANDBOX_URL}${endpoint}`,
      timeout: 180000, // 3 minutes
      ...(data && { data })
    };
    const response = await axios(config);
    return response.data;
  } catch (error) {
    console.error(`Sandbox API error: ${error.message}`);
    throw new Error(`Sandbox service error: ${error.response?.data?.detail || error.message}`);
  }
}

// Background review processor
async function processReview(sessionId) {
  try {
    const session = await getSession(sessionId);
    if (!session) {
      console.error(`Session ${sessionId} not found`);
      return;
    }

    // Emit progress
    const emitProgress = (update) => {
      io.to(sessionId).emit('progress', update);
    };

    // Update status
    await updateSession(sessionId, { status: 'analyzing', progress: 10 });
    emitProgress({ status: 'analyzing', progress: 10, message: 'Starting review...' });

    // Call Council for review
    emitProgress({ status: 'analyzing', progress: 20, message: 'Sending to Council agents...' });
    
    const councilRequest = {
      code: session.code,
      language: session.language,
      context: session.context,
      quality_gates: session.quality_gates
    };

    const councilResponse = await callCouncil('/council/review', councilRequest);

    // Update with Council results
    await updateSession(sessionId, {
      status: 'testing',
      progress: 60,
      agents: councilResponse.agents || []
    });
    emitProgress({ status: 'testing', progress: 60, message: 'Running tests in sandbox...' });

    // If tests need to be run, execute in sandbox
    if (councilResponse.test_code) {
      try {
        // Create sandbox
        const sandbox = await callSandbox('/sandbox/create', 'POST', {
          environment: session.language === 'python' ? 'python-3.11' : 'nodejs-18',
          timeout: 1800
        });

        const sandboxId = sandbox.sandbox_id;

        // Execute tests
        const testFiles = {
          ...councilResponse.code_files,
          ...councilResponse.test_files
        };

        const testCommands = session.language === 'python' 
          ? ['pip install -r requirements.txt', 'pytest']
          : ['npm install', 'npm test'];

        const testResult = await callSandbox(`/sandbox/${sandboxId}/execute`, 'POST', {
          files: testFiles,
          commands: testCommands,
          timeout: 300
        });

        // Clean up sandbox
        await callSandbox(`/sandbox/${sandboxId}`, 'DELETE');

        // Update with test results
        councilResponse.test_results = testResult.results;
      } catch (sandboxError) {
        console.error('Sandbox execution error:', sandboxError);
        councilResponse.test_results = {
          error: sandboxError.message
        };
      }
    }

    // Generate final report
    await updateSession(sessionId, {
      status: 'completed',
      progress: 100,
      report: councilResponse.report
    });

    emitProgress({
      status: 'completed',
      progress: 100,
      message: 'Review complete!',
      report: councilResponse.report
    });

  } catch (error) {
    console.error(`Review processing error for ${sessionId}:`, error);
    
    await updateSession(sessionId, {
      status: 'failed',
      error: error.message
    });

    io.to(sessionId).emit('error', {
      message: error.message
    });
  }
}

// API Routes

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'bridge',
    timestamp: new Date().toISOString()
  });
});

// Submit code for review
app.post('/api/v1/review/submit', async (req, res) => {
  try {
    const { code, language = 'javascript', context = '', quality_gates = ['qa', 'security', 'performance'] } = req.body;

    if (!code) {
      return res.status(400).json({ error: 'Code is required' });
    }

    // Create session
    const sessionId = `rev-${uuidv4()}`;
    const session = {
      id: sessionId,
      code,
      language,
      context,
      quality_gates,
      status: 'pending',
      progress: 0,
      agents: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    await saveSession(session);

    // Start background processing
    processReview(sessionId).catch(err => {
      console.error('Background review error:', err);
    });

    res.json({
      session_id: sessionId,
      status: 'pending',
      message: 'Review started'
    });

  } catch (error) {
    console.error('Submit error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get review status
app.get('/api/v1/review/:sessionId/status', async (req, res) => {
  try {
    const { sessionId } = req.params;
    const session = await getSession(sessionId);

    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }

    res.json({
      session_id: session.id,
      status: session.status,
      progress: session.progress,
      agents: session.agents.map(agent => ({
        name: agent.name,
        status: agent.status,
        score: agent.score
      }))
    });

  } catch (error) {
    console.error('Status error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get review report
app.get('/api/v1/review/:sessionId/report', async (req, res) => {
  try {
    const { sessionId } = req.params;
    const session = await getSession(sessionId);

    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }

    if (session.status !== 'completed') {
      return res.status(400).json({ error: 'Review not completed yet' });
    }

    res.json({
      session_id: session.id,
      report: session.report
    });

  } catch (error) {
    console.error('Report error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Apply fixes
app.post('/api/v1/review/:sessionId/fix', async (req, res) => {
  try {
    const { sessionId } = req.params;
    const { fix_priorities = ['critical', 'high'] } = req.body;

    const session = await getSession(sessionId);

    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }

    if (!session.report) {
      return res.status(400).json({ error: 'No report available' });
    }

    // Call Council to apply fixes
    const fixResponse = await callCouncil('/council/fix', {
      code: session.code,
      language: session.language,
      findings: session.report.priority_fixes.filter(f => 
        fix_priorities.includes(f.severity)
      )
    });

    res.json({
      session_id: sessionId,
      fixes_applied: fixResponse.fixes_applied,
      fixed_code: fixResponse.fixed_code,
      changes: fixResponse.changes,
      language: session.language,
      needs_review: fixResponse.needs_review
    });

  } catch (error) {
    console.error('Fix error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Delete review session
app.delete('/api/v1/review/:sessionId', async (req, res) => {
  try {
    const { sessionId } = req.params;
    await redis.del(`session:${sessionId}`);
    res.json({ message: 'Session deleted' });
  } catch (error) {
    console.error('Delete error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Quick security scan
app.post('/api/v1/scan/security', async (req, res) => {
  try {
    const { code, language = 'javascript' } = req.body;

    if (!code) {
      return res.status(400).json({ error: 'Code is required' });
    }

    // Call Security Agent directly
    const scanResult = await callCouncil('/council/security', {
      code,
      language
    });

    res.json({
      findings: scanResult.findings || []
    });

  } catch (error) {
    console.error('Security scan error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Quick performance scan
app.post('/api/v1/scan/performance', async (req, res) => {
  try {
    const { code, language = 'javascript' } = req.body;

    if (!code) {
      return res.status(400).json({ error: 'Code is required' });
    }

    // Call Performance Agent directly
    const scanResult = await callCouncil('/council/performance', {
      code,
      language
    });

    res.json({
      findings: scanResult.findings || [],
      benchmarks: scanResult.benchmarks || {}
    });

  } catch (error) {
    console.error('Performance scan error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Generate tests
app.post('/api/v1/generate/tests', async (req, res) => {
  try {
    const { code, language = 'javascript', test_framework = 'jest' } = req.body;

    if (!code) {
      return res.status(400).json({ error: 'Code is required' });
    }

    // Call QA Agent to generate tests
    const testResult = await callCouncil('/council/qa/generate-tests', {
      code,
      language,
      test_framework
    });

    res.json({
      test_code: testResult.test_code,
      test_count: testResult.test_count,
      test_cases: testResult.test_cases,
      coverage: testResult.coverage
    });

  } catch (error) {
    console.error('Test generation error:', error);
    res.status(500).json({ error: error.message });
  }
});

// WebSocket connection handling
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  socket.on('subscribe', (sessionId) => {
    socket.join(sessionId);
    console.log(`Client ${socket.id} subscribed to session ${sessionId}`);
  });

  socket.on('unsubscribe', (sessionId) => {
    socket.leave(sessionId);
    console.log(`Client ${socket.id} unsubscribed from session ${sessionId}`);
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Error handling
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: err.message
  });
});

// Start server
httpServer.listen(PORT, () => {
  console.log(`Bridge Service running on port ${PORT}`);
  console.log(`Council URL: ${COUNCIL_URL}`);
  console.log(`Sandbox URL: ${SANDBOX_URL}`);
  console.log(`Redis URL: ${REDIS_URL}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, closing server...');
  httpServer.close(() => {
    redis.disconnect();
    console.log('Server closed');
    process.exit(0);
  });
});
