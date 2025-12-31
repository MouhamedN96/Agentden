import { useEffect, useRef, useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Activity, 
  Shield, 
  Zap, 
  Layers,
  Terminal,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface AgentActivity {
  id: string;
  name: 'QA' | 'Security' | 'Performance' | 'Architecture';
  status: 'idle' | 'running' | 'complete' | 'error';
  progress: number;
  message: string;
  findings?: number;
}

interface SandboxLog {
  id: string;
  timestamp: Date;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
}

interface ExecutionWindowProps {
  reviewId?: string;
  isRunning: boolean;
}

const agentIcons = {
  QA: Activity,
  Security: Shield,
  Performance: Zap,
  Architecture: Layers,
};

const agentColors = {
  QA: 'hsl(var(--agent-qa))',
  Security: 'hsl(var(--agent-security))',
  Performance: 'hsl(var(--agent-performance))',
  Architecture: 'hsl(var(--agent-architecture))',
};

export function ExecutionWindow({ reviewId, isRunning }: ExecutionWindowProps) {
  const [agents, setAgents] = useState<AgentActivity[]>([
    {
      id: '1',
      name: 'QA',
      status: 'idle',
      progress: 0,
      message: 'Waiting to start...',
    },
    {
      id: '2',
      name: 'Security',
      status: 'idle',
      progress: 0,
      message: 'Waiting to start...',
    },
    {
      id: '3',
      name: 'Performance',
      status: 'idle',
      progress: 0,
      message: 'Waiting to start...',
    },
    {
      id: '4',
      name: 'Architecture',
      status: 'idle',
      progress: 0,
      message: 'Waiting to start...',
    },
  ]);

  const [logs, setLogs] = useState<SandboxLog[]>([]);
  const [showAgents, setShowAgents] = useState(true);
  const [showLogs, setShowLogs] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs to bottom
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Simulate agent activity (replace with real WebSocket data)
  useEffect(() => {
    if (!isRunning || !reviewId) return;

    const addLog = (type: SandboxLog['type'], message: string) => {
      setLogs(prev => [
        ...prev,
        {
          id: Math.random().toString(),
          timestamp: new Date(),
          type,
          message,
        },
      ]);
    };

    // Simulate review process
    const sequence = [
      { delay: 500, fn: () => {
        addLog('info', '$ Initializing code review...');
        setAgents(prev => prev.map((a, i) => 
          i === 0 ? { ...a, status: 'running', message: 'Analyzing code structure...' } : a
        ));
      }},
      { delay: 1500, fn: () => {
        addLog('info', '✓ Code parsed successfully');
        setAgents(prev => prev.map((a, i) => 
          i === 0 ? { ...a, progress: 30, message: 'Running test suite...' } : a
        ));
      }},
      { delay: 2500, fn: () => {
        addLog('success', '✓ 12/12 tests passed');
        setAgents(prev => prev.map((a, i) => 
          i === 0 ? { ...a, progress: 100, status: 'complete', message: 'Quality checks complete', findings: 3 } : 
          i === 1 ? { ...a, status: 'running', message: 'Scanning for vulnerabilities...' } : a
        ));
      }},
      { delay: 3500, fn: () => {
        addLog('warning', '⚠ Found 2 potential security issues');
        setAgents(prev => prev.map((a, i) => 
          i === 1 ? { ...a, progress: 60, message: 'Checking OWASP Top 10...' } : a
        ));
      }},
      { delay: 4500, fn: () => {
        addLog('info', '✓ No SQL injection vulnerabilities');
        addLog('info', '✓ No XSS vulnerabilities');
        setAgents(prev => prev.map((a, i) => 
          i === 1 ? { ...a, progress: 100, status: 'complete', message: 'Security scan complete', findings: 2 } :
          i === 2 ? { ...a, status: 'running', message: 'Analyzing performance...' } : a
        ));
      }},
      { delay: 5500, fn: () => {
        addLog('info', '⚡ Checking for N+1 queries...');
        setAgents(prev => prev.map((a, i) => 
          i === 2 ? { ...a, progress: 50, message: 'Profiling execution time...' } : a
        ));
      }},
      { delay: 6500, fn: () => {
        addLog('success', '✓ No performance bottlenecks detected');
        setAgents(prev => prev.map((a, i) => 
          i === 2 ? { ...a, progress: 100, status: 'complete', message: 'Performance analysis complete', findings: 1 } :
          i === 3 ? { ...a, status: 'running', message: 'Reviewing architecture...' } : a
        ));
      }},
      { delay: 7500, fn: () => {
        addLog('info', '✓ SOLID principles followed');
        addLog('info', '✓ Design patterns applied correctly');
        setAgents(prev => prev.map((a, i) => 
          i === 3 ? { ...a, progress: 100, status: 'complete', message: 'Architecture review complete', findings: 2 } : a
        ));
      }},
      { delay: 8000, fn: () => {
        addLog('success', '🎉 Code review complete! Overall score: 87/100');
      }},
    ];

    const timeouts = sequence.map(({ delay, fn }) => setTimeout(fn, delay));

    return () => timeouts.forEach(clearTimeout);
  }, [isRunning, reviewId]);

  const getStatusIcon = (status: AgentActivity['status']) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'hsl(var(--primary))' }} />;
      case 'complete':
        return <CheckCircle2 className="w-4 h-4" style={{ color: 'hsl(var(--success))' }} />;
      case 'error':
        return <AlertCircle className="w-4 h-4" style={{ color: 'hsl(var(--destructive))' }} />;
      default:
        return <div className="w-2 h-2 rounded-full bg-muted" />;
    }
  };

  const getLogIcon = (type: SandboxLog['type']) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'warning':
        return '⚠';
      case 'error':
        return '✗';
      default:
        return '$';
    }
  };

  const getLogColor = (type: SandboxLog['type']) => {
    switch (type) {
      case 'success':
        return 'text-[hsl(var(--success))]';
      case 'warning':
        return 'text-[hsl(var(--warning))]';
      case 'error':
        return 'text-[hsl(var(--destructive))]';
      default:
        return 'text-muted-foreground';
    }
  };

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Agent Activity Section */}
      <Card className="gradient-border">
        <div className="p-4">
          <button
            onClick={() => setShowAgents(!showAgents)}
            className="flex items-center justify-between w-full text-left group"
          >
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-lg">Agent Activity</h3>
            </div>
            {showAgents ? (
              <ChevronUp className="w-5 h-5 text-muted-foreground group-hover:text-foreground transition-colors" />
            ) : (
              <ChevronDown className="w-5 h-5 text-muted-foreground group-hover:text-foreground transition-colors" />
            )}
          </button>

          {showAgents && (
            <div className="mt-4 space-y-3">
              {agents.map((agent) => {
                const Icon = agentIcons[agent.name];
                return (
                  <div key={agent.id} className="command-block space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(agent.status)}
                        <Icon 
                          className="w-5 h-5" 
                          style={{ color: agentColors[agent.name] }}
                        />
                        <span className="font-medium">{agent.name} Agent</span>
                      </div>
                      {agent.findings !== undefined && agent.status === 'complete' && (
                        <Badge variant="secondary">
                          {agent.findings} {agent.findings === 1 ? 'finding' : 'findings'}
                        </Badge>
                      )}
                    </div>

                    {agent.status === 'running' && (
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm text-muted-foreground">
                          <span>{agent.message}</span>
                          <span>{agent.progress}%</span>
                        </div>
                        <div className="h-1 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary transition-all duration-300"
                            style={{ 
                              width: `${agent.progress}%`,
                              boxShadow: '0 0 10px hsl(var(--glow-primary))'
                            }}
                          />
                        </div>
                      </div>
                    )}

                    {agent.status !== 'running' && (
                      <p className="text-sm text-muted-foreground">{agent.message}</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </Card>

      {/* Sandbox Output Section */}
      <Card className="gradient-border flex-1 flex flex-col">
        <div className="p-4 border-b border-[hsl(var(--border))]">
          <button
            onClick={() => setShowLogs(!showLogs)}
            className="flex items-center justify-between w-full text-left group"
          >
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-lg">Sandbox Output</h3>
            </div>
            {showLogs ? (
              <ChevronUp className="w-5 h-5 text-muted-foreground group-hover:text-foreground transition-colors" />
            ) : (
              <ChevronDown className="w-5 h-5 text-muted-foreground group-hover:text-foreground transition-colors" />
            )}
          </button>
        </div>

        {showLogs && (
          <ScrollArea className="flex-1 p-4">
            <div className="terminal-output space-y-1">
              {logs.length === 0 ? (
                <div className="text-muted-foreground text-sm">
                  Waiting for review to start...
                </div>
              ) : (
                logs.map((log) => (
                  <div key={log.id} className="terminal-line flex items-start gap-3 font-mono text-sm">
                    <span className={getLogColor(log.type)}>
                      {getLogIcon(log.type)}
                    </span>
                    <span className="text-muted-foreground text-xs">
                      {log.timestamp.toLocaleTimeString()}
                    </span>
                    <span className="flex-1">{log.message}</span>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </ScrollArea>
        )}
      </Card>
    </div>
  );
}
