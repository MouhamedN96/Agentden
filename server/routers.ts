import { COOKIE_NAME } from "@shared/const";
import { z } from "zod";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, protectedProcedure, router } from "./_core/trpc";

// Mock findings generator
function getMockFindings(agentType: string) {
  const findings: any[] = [];
  
  if (agentType === "security") {
    findings.push({
      severity: "critical",
      title: "SQL Injection Vulnerability",
      description: "Direct string concatenation in SQL query allows SQL injection attacks",
      lineNumber: 15,
      category: "SQL Injection",
      suggestedFix: "Use parameterized queries or prepared statements",
    });
  } else if (agentType === "qa") {
    findings.push({
      severity: "high",
      title: "Missing Error Handling",
      description: "Function does not handle potential errors from async operations",
      lineNumber: 23,
      category: "Error Handling",
      suggestedFix: "Add try-catch block around async operations",
    });
  } else if (agentType === "performance") {
    findings.push({
      severity: "medium",
      title: "N+1 Query Problem",
      description: "Loop contains database query that will execute N times",
      lineNumber: 42,
      category: "N+1 Query",
      suggestedFix: "Use batch query or JOIN to fetch all data at once",
    });
  } else if (agentType === "architecture") {
    findings.push({
      severity: "low",
      title: "Code Duplication",
      description: "Similar logic repeated in multiple places",
      lineNumber: 67,
      category: "Code Smell",
      suggestedFix: "Extract common logic into reusable function",
    });
  }
  
  return findings;
}

export const appRouter = router({
    // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  review: router({
    // Submit a new code review
    submit: protectedProcedure
      .input(z.object({
        code: z.string().min(1),
        language: z.string().min(1),
        qualityGates: z.array(z.enum(["qa", "security", "performance", "architecture"])).optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        const { createReview, createAgentResult } = await import("./db");
        
        // Create review record
        const reviewId = await createReview({
          userId: ctx.user.id,
          code: input.code,
          language: input.language,
          status: "pending",
        });
        
        // Create agent result records for each quality gate
        const gates = input.qualityGates || ["qa", "security", "performance", "architecture"];
        await Promise.all(
          gates.map(gate =>
            createAgentResult({
              reviewId,
              agentType: gate as any,
              status: "pending",
            })
          )
        );
        
        // TODO: Trigger actual review process via AgentDen backend
        // For now, we'll simulate it with mock data
        
        return { reviewId, status: "pending" };
      }),
    
    // Get review by ID with all details
    getById: protectedProcedure
      .input(z.object({ id: z.number() }))
      .query(async ({ ctx, input }) => {
        const { getReviewById, getAgentResultsByReviewId, getFindingsByAgentResultId } = await import("./db");
        
        const review = await getReviewById(input.id);
        if (!review || review.userId !== ctx.user.id) {
          throw new Error("Review not found");
        }
        
        const agentResults = await getAgentResultsByReviewId(review.id);
        
        // Get findings for each agent result
        const resultsWithFindings = await Promise.all(
          agentResults.map(async (result) => {
            const findings = await getFindingsByAgentResultId(result.id);
            return { ...result, findings };
          })
        );
        
        return {
          ...review,
          agents: resultsWithFindings,
        };
      }),
    
    // Get user's review history
    list: protectedProcedure
      .input(z.object({
        limit: z.number().optional(),
      }).optional())
      .query(async ({ ctx, input }) => {
        const { getUserReviews } = await import("./db");
        return getUserReviews(ctx.user.id, input?.limit);
      }),
    
    // Simulate review progress (for demo purposes)
    simulateProgress: protectedProcedure
      .input(z.object({ reviewId: z.number() }))
      .mutation(async ({ ctx, input }) => {
        const { getReviewById, updateReviewStatus, getAgentResultsByReviewId, updateAgentResult, createFinding } = await import("./db");
        
        const review = await getReviewById(input.reviewId);
        if (!review || review.userId !== ctx.user.id) {
          throw new Error("Review not found");
        }
        
        // Update review to in_progress
        await updateReviewStatus(input.reviewId, "in_progress");
        
        // Simulate agent processing
        const agents = await getAgentResultsByReviewId(input.reviewId);
        
        for (const agent of agents) {
          // Update agent to in_progress
          await updateAgentResult(agent.id, {
            status: "in_progress",
            startedAt: new Date(),
          });
          
          // Simulate some findings
          const mockFindings = getMockFindings(agent.agentType);
          for (const finding of mockFindings) {
            await createFinding({
              agentResultId: agent.id,
              ...finding,
            });
          }
          
          // Complete agent
          await updateAgentResult(agent.id, {
            status: "completed",
            score: Math.floor(Math.random() * 30) + 70, // 70-100
            summary: `${agent.agentType} analysis completed`,
            completedAt: new Date(),
          });
        }
        
        // Complete review
        await updateReviewStatus(input.reviewId, "completed", 85);
        
        return { success: true };
      }),
  }),
});

export type AppRouter = typeof appRouter;
