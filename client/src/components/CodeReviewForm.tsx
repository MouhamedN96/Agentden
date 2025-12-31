import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { trpc } from "@/lib/trpc";
import Editor from "@monaco-editor/react";
import { AlertCircle, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";
import { useLocation } from "wouter";
import { toast } from "sonner";

const LANGUAGES = [
  { value: "javascript", label: "JavaScript" },
  { value: "typescript", label: "TypeScript" },
  { value: "python", label: "Python" },
  { value: "go", label: "Go" },
  { value: "rust", label: "Rust" },
  { value: "java", label: "Java" },
  { value: "csharp", label: "C#" },
  { value: "php", label: "PHP" },
];

const QUALITY_GATES = [
  { id: "qa", label: "QA Agent", description: "Test coverage, error handling" },
  { id: "security", label: "Security Agent", description: "OWASP, SQL injection, XSS" },
  { id: "performance", label: "Performance Agent", description: "N+1 queries, optimization" },
  { id: "architecture", label: "Architecture Agent", description: "SOLID, design patterns" },
];

export function CodeReviewForm() {
  const [, setLocation] = useLocation();
  const [code, setCode] = useState(`function login(username, password) {
  const user = db.query(\`SELECT * FROM users WHERE username='\${username}'\`);
  return user && user.password === password;
}`);
  const [language, setLanguage] = useState("javascript");
  const [selectedGates, setSelectedGates] = useState<string[]>(["qa", "security", "performance", "architecture"]);

  const submitMutation = trpc.review.submit.useMutation({
    onSuccess: (data) => {
      toast.success("Review submitted successfully!");
      // Navigate to review page
      setLocation(`/review/${data.reviewId}`);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to submit review");
    },
  });

  const handleSubmit = () => {
    if (!code.trim()) {
      toast.error("Please enter some code to review");
      return;
    }

    if (selectedGates.length === 0) {
      toast.error("Please select at least one quality gate");
      return;
    }

    submitMutation.mutate({
      code,
      language,
      qualityGates: selectedGates as any[],
    });
  };

  const toggleGate = (gateId: string) => {
    setSelectedGates((prev) =>
      prev.includes(gateId) ? prev.filter((id) => id !== gateId) : [...prev, gateId]
    );
  };

  return (
    <Card className="border-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          Submit Code for Review
        </CardTitle>
        <CardDescription>
          Paste your code below and select quality gates for AI analysis
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Language Selector */}
        <div className="space-y-2">
          <Label htmlFor="language">Programming Language</Label>
          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger id="language" className="w-full">
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
        </div>

        {/* Code Editor */}
        <div className="space-y-2">
          <Label>Code</Label>
          <div className="border rounded-lg overflow-hidden bg-card">
            <Editor
              height="400px"
              language={language}
              value={code}
              onChange={(value) => setCode(value || "")}
              theme="vs-light"
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: "on",
                roundedSelection: true,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                padding: { top: 16, bottom: 16 },
              }}
            />
          </div>
        </div>

        {/* Quality Gates */}
        <div className="space-y-3">
          <Label>Quality Gates</Label>
          <div className="grid gap-3 sm:grid-cols-2">
            {QUALITY_GATES.map((gate) => (
              <div
                key={gate.id}
                className={`flex items-start gap-3 p-4 rounded-lg border-2 transition-all cursor-pointer ${
                  selectedGates.includes(gate.id)
                    ? "border-primary bg-primary/5"
                    : "border-[hsl(var(--border))] hover:border-primary/50"
                }`}
                onClick={() => toggleGate(gate.id)}
              >
                <Checkbox
                  id={gate.id}
                  checked={selectedGates.includes(gate.id)}
                  onCheckedChange={() => toggleGate(gate.id)}
                  className="mt-1"
                />
                <div className="flex-1">
                  <label
                    htmlFor={gate.id}
                    className="text-sm font-medium leading-none cursor-pointer"
                  >
                    {gate.label}
                  </label>
                  <p className="text-xs text-muted-foreground mt-1">{gate.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Submit Button */}
        <Button
          onClick={handleSubmit}
          disabled={submitMutation.isPending}
          className="w-full h-12 text-base"
          size="lg"
        >
          {submitMutation.isPending ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Submitting...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5 mr-2" />
              Start AI Review
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
