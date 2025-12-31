import { int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Code reviews submitted by users for AI agent analysis
 */
export const reviews = mysqlTable("reviews", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().references(() => users.id),
  code: text("code").notNull(),
  language: varchar("language", { length: 50 }).notNull(),
  status: mysqlEnum("status", ["pending", "in_progress", "completed", "failed"]).default("pending").notNull(),
  overallScore: int("overallScore"), // 0-100
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  completedAt: timestamp("completedAt"),
});

export type Review = typeof reviews.$inferSelect;
export type InsertReview = typeof reviews.$inferInsert;

/**
 * Individual agent analysis results (QA, Security, Performance, Architecture)
 */
export const agentResults = mysqlTable("agentResults", {
  id: int("id").autoincrement().primaryKey(),
  reviewId: int("reviewId").notNull().references(() => reviews.id),
  agentType: mysqlEnum("agentType", ["qa", "security", "performance", "architecture"]).notNull(),
  status: mysqlEnum("status", ["pending", "in_progress", "completed", "failed"]).default("pending").notNull(),
  score: int("score"), // 0-100
  summary: text("summary"),
  startedAt: timestamp("startedAt"),
  completedAt: timestamp("completedAt"),
});

export type AgentResult = typeof agentResults.$inferSelect;
export type InsertAgentResult = typeof agentResults.$inferInsert;

/**
 * Detailed findings from agent analysis
 */
export const findings = mysqlTable("findings", {
  id: int("id").autoincrement().primaryKey(),
  agentResultId: int("agentResultId").notNull().references(() => agentResults.id),
  severity: mysqlEnum("severity", ["critical", "high", "medium", "low", "info"]).notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  description: text("description").notNull(),
  lineNumber: int("lineNumber"),
  suggestedFix: text("suggestedFix"),
  category: varchar("category", { length: 100 }), // e.g., "SQL Injection", "N+1 Query"
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type Finding = typeof findings.$inferSelect;
export type InsertFinding = typeof findings.$inferInsert;