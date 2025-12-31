import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { trpc } from "@/lib/trpc";
import { Clock, Code2, Eye, Loader2 } from "lucide-react";
import { useLocation } from "wouter";
import { formatDistanceToNow } from "date-fns";

export function ReviewHistory() {
  const [, setLocation] = useLocation();
  const { data: reviews, isLoading } = trpc.review.list.useQuery({ limit: 50 });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (!reviews || reviews.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <Code2 className="w-12 h-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-semibold mb-2">No reviews yet</h3>
          <p className="text-sm text-muted-foreground">
            Submit your first code review to get started
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {reviews.map((review) => (
        <Card key={review.id} className="hover:shadow-md transition-shadow">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Code2 className="w-5 h-5" />
                  {review.language.charAt(0).toUpperCase() + review.language.slice(1)} Review
                </CardTitle>
                <CardDescription className="flex items-center gap-2">
                  <Clock className="w-3 h-3" />
                  {formatDistanceToNow(new Date(review.createdAt), { addSuffix: true })}
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={review.status} />
                {review.overallScore && (
                  <ScoreBadge score={review.overallScore} />
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                {review.code.split("\n").length} lines of code
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setLocation(`/review/${review.id}`)}
              >
                <Eye className="w-4 h-4 mr-2" />
                View Report
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
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
  let variant: "default" | "secondary" | "destructive" | "outline" = "default";
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
