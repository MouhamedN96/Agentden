import { useState } from 'react';
import { useAuth } from '@/_core/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ExecutionWindow } from '@/components/ExecutionWindow';
import { Editor } from '@monaco-editor/react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Code2, 
  Play, 
  History,
  User,
  TrendingUp,
  CheckCircle2,
  Star
} from 'lucide-react';
import { trpc } from '@/lib/trpc';
import { toast } from 'sonner';

const LANGUAGES = [
  { value: 'javascript', label: 'JavaScript', monaco: 'javascript' },
  { value: 'typescript', label: 'TypeScript', monaco: 'typescript' },
  { value: 'python', label: 'Python', monaco: 'python' },
  { value: 'go', label: 'Go', monaco: 'go' },
  { value: 'rust', label: 'Rust', monaco: 'rust' },
  { value: 'java', label: 'Java', monaco: 'java' },
];

const QUALITY_GATES: Array<{ id: 'qa' | 'security' | 'performance' | 'architecture'; label: string; description: string }> = [
  { id: 'qa', label: 'QA', description: 'Code quality & testing' },
  { id: 'security', label: 'Security', description: 'Vulnerability scanning' },
  { id: 'performance', label: 'Performance', description: 'Optimization analysis' },
  { id: 'architecture', label: 'Architecture', description: 'Design patterns' },
];

export default function DashboardV2() {
  const { user, loading } = useAuth();
  const [code, setCode] = useState('// Write or paste your code here\n\nfunction example() {\n  return "Hello, AgentDen!";\n}\n');
  const [language, setLanguage] = useState('javascript');
  type QualityGate = 'qa' | 'security' | 'performance' | 'architecture';
  const [selectedGates, setSelectedGates] = useState<QualityGate[]>(['qa', 'security', 'performance', 'architecture']);
  const [currentReviewId, setCurrentReviewId] = useState<string | undefined>();
  const [isReviewing, setIsReviewing] = useState(false);

  const submitReview = trpc.review.submit.useMutation({
    onSuccess: (data) => {
      toast.success('Review started!');
      setCurrentReviewId(data.reviewId.toString());
      setIsReviewing(true);
      
      // Simulate review completion after 8 seconds
      setTimeout(() => {
        setIsReviewing(false);
        toast.success('Review complete!', {
          description: 'Check the results in the execution window',
        });
      }, 8000);
    },
    onError: (error) => {
      toast.error('Failed to start review', {
        description: error.message,
      });
    },
  });

  const reviewList = trpc.review.list.useQuery();
  
  const stats = {
    total: reviewList.data?.length || 0,
    passed: reviewList.data?.filter(r => r.status === 'completed' && (r.overallScore || 0) >= 70).length || 0,
    avgScore: reviewList.data && reviewList.data.length > 0
      ? Math.round(reviewList.data.reduce((acc, r) => acc + (r.overallScore || 0), 0) / reviewList.data.length)
      : 0,
  };

  const handleSubmit = () => {
    if (!code.trim()) {
      toast.error('Please enter some code to review');
      return;
    }

    if (selectedGates.length === 0) {
      toast.error('Please select at least one quality gate');
      return;
    }

    submitReview.mutate({
      code,
      language,
      qualityGates: selectedGates,
    });
  };

  const toggleGate = (gateId: QualityGate) => {
    setSelectedGates(prev =>
      prev.includes(gateId)
        ? prev.filter(id => id !== gateId)
        : [...prev, gateId]
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background grid-background">
      {/* Header */}
      <header className="border-b border-[hsl(var(--border))] glass sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Code2 className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gradient">AgentDen</h1>
                <p className="text-xs text-muted-foreground">AI Code Review Platform</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {user && (
                <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-card border border-[hsl(var(--border))]">
                  <User className="w-5 h-5 text-primary" />
                  <span className="text-sm font-medium">{user.name || user.email}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="border-b border-[hsl(var(--border))] bg-card/50">
        <div className="container mx-auto px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-xs text-muted-foreground">Total Reviews</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[hsl(var(--success))]/10 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-[hsl(var(--success))]" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.passed}</p>
                <p className="text-xs text-muted-foreground">Passed</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[hsl(var(--warning))]/10 flex items-center justify-center">
                <Star className="w-5 h-5 text-[hsl(var(--warning))]" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.avgScore}</p>
                <p className="text-xs text-muted-foreground">Avg Score</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Split Panel */}
      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr,400px] gap-6 h-[calc(100vh-280px)]">
          {/* Left Panel - Code Editor */}
          <Card className="gradient-border flex flex-col overflow-hidden">
            <div className="p-4 border-b border-[hsl(var(--border))] flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Select value={language} onValueChange={setLanguage}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LANGUAGES.map((lang) => (
                      <SelectItem key={lang.value} value={lang.value}>
                        {lang.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <div className="flex gap-2">
                  {QUALITY_GATES.map((gate) => (
                    <Button
                      key={gate.id}
                      variant={selectedGates.includes(gate.id) ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => toggleGate(gate.id)}
                      className="text-xs"
                    >
                      {gate.label}
                    </Button>
                  ))}
                </div>
              </div>

              <Button
                onClick={handleSubmit}
                disabled={isReviewing || submitReview.isPending}
                className="gap-2"
              >
                {isReviewing || submitReview.isPending ? (
                  <>
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    Reviewing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Start Review
                  </>
                )}
              </Button>
            </div>

            <div className="flex-1 overflow-hidden">
              <Editor
                height="100%"
                language={LANGUAGES.find(l => l.value === language)?.monaco || 'javascript'}
                value={code}
                onChange={(value) => setCode(value || '')}
                theme="vs-dark"
                options={{
                  minimap: { enabled: true },
                  fontSize: 14,
                  lineNumbers: 'on',
                  rulers: [80, 120],
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  tabSize: 2,
                  wordWrap: 'on',
                }}
              />
            </div>
          </Card>

          {/* Right Panel - Execution Window */}
          <div className="flex flex-col h-full">
            <ExecutionWindow reviewId={currentReviewId} isRunning={isReviewing} />
          </div>
        </div>
      </div>
    </div>
  );
}
