import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { ArrowRight, Code2, Loader2, Shield, Sparkles, Zap } from "lucide-react";
import { getLoginUrl } from "@/const";
import { useLocation } from "wouter";
import { useEffect } from "react";

/**
 * All content in this page are only for example, replace with your own feature implementation
 * When building pages, remember your instructions in Frontend Workflow, Frontend Best Practices, Design Guide and Common Pitfalls
 */
export default function Home() {
  const { user, loading, isAuthenticated } = useAuth();
  const [, setLocation] = useLocation();
  
  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (isAuthenticated && user) {
      setLocation("/dashboard");
    }
  }, [isAuthenticated, user, setLocation]);

  // If theme is switchable in App.tsx, we can implement theme toggling like this:
  // const { theme, toggleTheme } = useTheme();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      {/* Hero Section */}
      <div className="container py-20">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          {/* Logo */}
          <div className="flex items-center justify-center">
            <div className="flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-primary to-accent shadow-lg">
              <Sparkles className="w-10 h-10 text-primary-foreground" />
            </div>
          </div>
          
          {/* Headline */}
          <div className="space-y-4">
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight">
              AI-Powered Code Review
              <span className="block text-primary mt-2">Built for Excellence</span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Get instant, comprehensive code analysis from specialized AI agents.
              Security, performance, quality, and architecture—all in one place.
            </p>
          </div>
          
          {/* CTA */}
          <div className="flex items-center justify-center gap-4">
            <Button size="lg" className="h-14 px-8 text-lg" asChild>
              <a href={getLoginUrl()}>
                Get Started
                <ArrowRight className="w-5 h-5 ml-2" />
              </a>
            </Button>
          </div>
        </div>
        
        {/* Features */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mt-20 max-w-6xl mx-auto">
          <FeatureCard
            icon={<Shield className="w-6 h-6" />}
            title="Security"
            description="OWASP Top 10, SQL injection, XSS detection"
          />
          <FeatureCard
            icon={<Zap className="w-6 h-6" />}
            title="Performance"
            description="N+1 queries, optimization opportunities"
          />
          <FeatureCard
            icon={<Code2 className="w-6 h-6" />}
            title="Quality"
            description="Test coverage, error handling, best practices"
          />
          <FeatureCard
            icon={<Sparkles className="w-6 h-6" />}
            title="Architecture"
            description="SOLID principles, design patterns, code smells"
          />
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="p-6 rounded-xl bg-card border-2 hover:border-primary/50 transition-colors">
      <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10 text-primary mb-4">
        {icon}
      </div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
