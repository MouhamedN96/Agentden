import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Code2, History, Sparkles } from "lucide-react";
import { useState } from "react";
import { CodeReviewForm } from "@/components/CodeReviewForm";
import { ReviewHistory } from "@/components/ReviewHistory";

export default function Dashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("review");

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent">
                <Sparkles className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-semibold">AgentDen</h1>
                <p className="text-sm text-muted-foreground">AI Code Review</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium">{user?.name || "User"}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-primary-foreground font-semibold">
                {user?.name?.[0]?.toUpperCase() || "U"}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-2 h-12">
            <TabsTrigger value="review" className="gap-2">
              <Code2 className="w-4 h-4" />
              New Review
            </TabsTrigger>
            <TabsTrigger value="history" className="gap-2">
              <History className="w-4 h-4" />
              History
            </TabsTrigger>
          </TabsList>

          <TabsContent value="review" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Stats Cards */}
              <Card className="bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
                <CardHeader className="pb-3">
                  <CardDescription>Total Reviews</CardDescription>
                  <CardTitle className="text-3xl">0</CardTitle>
                </CardHeader>
              </Card>
              
              <Card className="bg-gradient-to-br from-success/5 to-success/10 border-success/20">
                <CardHeader className="pb-3">
                  <CardDescription>Passed</CardDescription>
                  <CardTitle className="text-3xl text-success">0</CardTitle>
                </CardHeader>
              </Card>
              
              <Card className="bg-gradient-to-br from-warning/5 to-warning/10 border-warning/20">
                <CardHeader className="pb-3">
                  <CardDescription>Avg Score</CardDescription>
                  <CardTitle className="text-3xl text-warning">--</CardTitle>
                </CardHeader>
              </Card>
            </div>

            {/* Code Review Form */}
            <CodeReviewForm />
          </TabsContent>

          <TabsContent value="history">
            <ReviewHistory />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
