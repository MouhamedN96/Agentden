import { describe, expect, it } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

type AuthenticatedUser = NonNullable<TrpcContext["user"]>;

function createAuthContext(): { ctx: TrpcContext } {
  const user: AuthenticatedUser = {
    id: 1,
    openId: "test-user",
    email: "test@example.com",
    name: "Test User",
    loginMethod: "manus",
    role: "user",
    createdAt: new Date(),
    updatedAt: new Date(),
    lastSignedIn: new Date(),
  };

  const ctx: TrpcContext = {
    user,
    req: {
      protocol: "https",
      headers: {},
    } as TrpcContext["req"],
    res: {
      clearCookie: () => {},
    } as TrpcContext["res"],
  };

  return { ctx };
}

describe("review.submit", () => {
  it("creates a new code review with all quality gates", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.review.submit({
      code: "function test() { return true; }",
      language: "javascript",
      qualityGates: ["qa", "security", "performance", "architecture"],
    });

    expect(result).toHaveProperty("reviewId");
    expect(result.reviewId).toBeGreaterThan(0);
    expect(result.status).toBe("pending");
  });

  it("creates a review with default quality gates when none specified", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.review.submit({
      code: "console.log('hello');",
      language: "javascript",
    });

    expect(result).toHaveProperty("reviewId");
    expect(result.status).toBe("pending");
  });
});

describe("review.getById", () => {
  it("retrieves a review with all agent results", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    // First create a review
    const submitResult = await caller.review.submit({
      code: "function add(a, b) { return a + b; }",
      language: "javascript",
      qualityGates: ["qa", "security"],
    });

    // Then retrieve it
    const review = await caller.review.getById({ id: submitResult.reviewId });

    expect(review).toHaveProperty("id", submitResult.reviewId);
    expect(review).toHaveProperty("code");
    expect(review).toHaveProperty("language", "javascript");
    expect(review).toHaveProperty("agents");
    expect(review.agents).toHaveLength(2);
    expect(review.agents[0]).toHaveProperty("agentType");
    expect(review.agents[0]).toHaveProperty("status", "pending");
  });
});

describe("review.list", () => {
  it("returns user's review history", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    // Create a few reviews
    await caller.review.submit({
      code: "test1",
      language: "javascript",
    });
    await caller.review.submit({
      code: "test2",
      language: "python",
    });

    // Get list
    const reviews = await caller.review.list({ limit: 10 });

    expect(Array.isArray(reviews)).toBe(true);
    expect(reviews.length).toBeGreaterThanOrEqual(2);
    expect(reviews[0]).toHaveProperty("id");
    expect(reviews[0]).toHaveProperty("language");
  });
});
