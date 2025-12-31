import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { trpc } from "@/lib/trpc";
import { AlertTriangle, ArrowLeft, CheckCircle2, Clock, Code2, Info, Loader2, Play, Shield, Sparkles, XCircle, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useRoute } from "wouter";
import { toast } from "sonner";
import Editor from "@monaco-editor/react";

export default function ReviewDetail() {
  const [, params] = useRoute("/review/:id");
  const [, setLocation] = useLocation();
  const reviewId = params?.id ? parseInt(params.id) : 0;

  const { data: review, isLoading, refetch } = trpc.review.getById.useQuery(
    { id: reviewId },
    { enabled: reviewId > 0 }
  );

  const simulateMutation = trpc.review.simulateProgress.useMutation({
    onSuccess: () => {
      toast.success("Review completed!");
      refetch();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to complete review");
    },
  });

  // Auto-trigger simulation for pending reviews
  useEffect(() => {
    if (review?.status === "pending" && !simulateMutation.isPending) {
      const timer = setTimeout(() => {
        simulateMutation.mutate({ reviewId });
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [review?.status, reviewId]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!review) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center">
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">Review not found</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isProcessing = review.status === "pending" || review.status === "in_progress";

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => setLocation("/dashboard")}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div className="flex-1">
              <h1 className="text-xl font-semibold">Code Review #{review.id}</h1>
              <p className="text-sm text-muted-foreground">
                {review.language.charAt(0).toUpperCase() + review.language.slice(1)}
              </p>
            </div>
            <StatusBadge status={review.status} />
            {review.overallScore && <ScoreBadge score={review.overallScore} />}
          </div>
        </div>
      </header>

      <main className="container py-8 space-y-6">
        {/* Processing State */}
        {isProcessing && (
          <Card className="border-primary/50 bg-primary/5">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
                <div className="flex-1">
                  <p className="font-medium">AI agents are analyzing your code...</p>
                  <p className="text-sm text-muted-foreground">This usually takes 10-30 seconds</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Agent Status Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {review.agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>

        {/* Code and Findings */}
        <Tabs defaultValue="code" className="space-y-4">
          <TabsList>
            <TabsTrigger value="code">Original Code</TabsTrigger>
            <TabsTrigger value="findings">Findings ({getTotalFindings(review.agents)})</TabsTrigger>
          </TabsList>

          <TabsContent value="code">
            <Card>
              <CardHeader>
                <CardTitle>Submitted Code</CardTitle>
                <CardDescription>{review.code.split("\n").length} lines</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border rounded-lg overflow-hidden">
                  <Editor
                    height="400px"
                    language={review.language}
                    value={review.code}
                    theme="vs-light"
                    options={{
                      readOnly: true,
                      minimap: { enabled: false },
                      fontSize: 14,
                      lineNumbers: "on",
                      scrollBeyondLastLine: false,
                    }}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="findings" className="space-y-4">
            {review.agents.map((agent) => (
              <AgentFindings key={agent.id} agent={agent} />
            ))}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

function AgentCard({ agent }: { agent: any }) {
  const icons = {
    qa: <CheckCircle2 className="w-5 h-5" />,
    security: <Shield className="w-5 h-5" />,
    performance: <Zap className="w-5 h-5" />,
    architecture: <Sparkles className="w-5 h-5" />,
  };

  const colors = {
    qa: "from-success/10 to-success/5 border-success/30",
    security: "from-destructive/10 to-destructive/5 border-destructive/30",
    performance: "from-warning/10 to-warning/5 border-warning/30",
    architecture: "from-info/10 to-info/5 border-info/30",
  };

  const isComplete = agent.status === "completed";
  const isProcessing = agent.status === "in_progress";

  return (
    <Card className={`bg-gradient-to-br ${colors[agent.agentType as keyof typeof colors]}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {icons[agent.agentType as keyof typeof icons]}
            <CardTitle className="text-base capitalize">{agent.agentType}</CardTitle>
          </div>
          {isProcessing && <Loader2 className="w-4 h-4 animate-spin" />}
          {isComplete && agent.score && (
            <span className="text-2xl font-bold">{agent.score}</span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isComplete && agent.score && (
          <Progress value={agent.score} className="h-2" />
        )}
        {isProcessing && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="w-3 h-3" />
            Analyzing...
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function AgentFindings({ agent }: { agent: any }) {
  if (!agent.findings || agent.findings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="capitalize">{agent.agentType} Agent</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No issues found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="capitalize flex items-center gap-2">
          {agent.agentType} Agent
          <Badge variant="secondary">{agent.findings.length} findings</Badge>
        </CardTitle>
        {agent.summary && (
          <CardDescription>{agent.summary}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {agent.findings.map((finding: any, idx: number) => (
          <FindingCard key={idx} finding={finding} />
        ))}
      </CardContent>
    </Card>
  );
}

function FindingCard({ finding }: { finding: any }) {
  const severityConfig = {
    critical: { icon: <XCircle className="w-5 h-5" />, color: "text-destructive", bg: "bg-destructive/10" },
    high: { icon: <AlertTriangle className="w-5 h-5" />, color: "text-destructive", bg: "bg-destructive/10" },
    medium: { icon: <AlertTriangle className="w-5 h-5" />, color: "text-warning", bg: "bg-warning/10" },
    low: { icon: <Info className="w-5 h-5" />, color: "text-info", bg: "bg-info/10" },
    info: { icon: <Info className="w-5 h-5" />, color: "text-muted-foreground", bg: "bg-muted" },
  };

  const config = severityConfig[finding.severity as keyof typeof severityConfig];

  return (
    <div className={`p-4 rounded-lg border-2 ${config.bg}`}>
      <div className="flex items-start gap-3">
        <div className={config.color}>{config.icon}</div>
        <div className="flex-1 space-y-2">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h4 className="font-semibold">{finding.title}</h4>
              {finding.lineNumber && (
                <p className="text-xs text-muted-foreground">Line {finding.lineNumber}</p>
              )}
            </div>
            <Badge variant="outline" className="capitalize">
              {finding.severity}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">{finding.description}</p>
          {finding.suggestedFix && (
            <div className="mt-3 p-3 bg-card rounded border">
              <p className="text-xs font-medium text-muted-foreground mb-1">Suggested Fix:</p>
              <p className="text-sm">{finding.suggestedFix}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    pending: { label: "Pending", variant: "secondary" },
    in_progress: { label: "In Progress", variant: "default" },
    completed: { label: "Completed", variant: "outline" },
    failed: { label: "Failed", variant: "destructive" },
  };

  const config = variants[status] || variants.pending;

  return (
    <Badge variant={config.variant} className="capitalize">
      {config.label}
    </Badge>
  );
}

function ScoreBadge({ score }: { score: number }) {
  let className = "";

  if (score >= 80) {
    className = "bg-success text-success-foreground";
  } else if (score >= 60) {
    className = "bg-warning text-warning-foreground";
  } else {
    className = "bg-destructive text-destructive-foreground";
  }

  return (
    <Badge className={className}>
      Score: {score}/100
    </Badge>
  );
}

function getTotalFindings(agents: any[]) {
  return agents.reduce((total, agent) => total + (agent.findings?.length || 0), 0);
}
