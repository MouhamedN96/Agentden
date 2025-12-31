#!/usr/bin/env node

/**
 * MCP Server for Code Quality Bridge
 * Integrates Claude Code with Council agents for code review
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";

// Configuration
const BRIDGE_URL = process.env.BRIDGE_URL || "http://localhost:8004";
const API_KEY = process.env.BRIDGE_API_KEY || "";

// MCP Server
const server = new Server(
  {
    name: "code-quality-bridge",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Helper: Make API request to bridge
async function callBridge(endpoint, method = "GET", data = null) {
  try {
    const config = {
      method,
      url: `${BRIDGE_URL}${endpoint}`,
      headers: {
        "Content-Type": "application/json",
        ...(API_KEY && { "Authorization": `Bearer ${API_KEY}` }),
      },
      ...(data && { data }),
    };

    const response = await axios(config);
    return response.data;
  } catch (error) {
    throw new Error(
      `Bridge API error: ${error.response?.data?.detail || error.message}`
    );
  }
}

// Tool 1: Submit code for review
async function submitCodeForReview(args) {
  const { code, language, context, quality_gates } = args;

  const response = await callBridge("/api/v1/review/submit", "POST", {
    code,
    language: language || "javascript",
    context: context || "",
    quality_gates: quality_gates || ["security", "qa", "performance"],
  });

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(
          {
            session_id: response.session_id,
            status: response.status,
            message: `Code review started. Session ID: ${response.session_id}`,
            next_step: "Use get_review_status to check progress",
          },
          null,
          2
        ),
      },
    ],
  };
}

// Tool 2: Get review status
async function getReviewStatus(args) {
  const { session_id } = args;

  const response = await callBridge(`/api/v1/review/${session_id}/status`);

  const statusText = `
Review Status: ${response.status}
Progress: ${response.progress}%

Agents:
${response.agents
  .map(
    (agent) =>
      `  - ${agent.name}: ${agent.status} ${
        agent.score !== null ? `(Score: ${agent.score}/100)` : ""
      }`
  )
  .join("\n")}

${
  response.status === "completed"
    ? "✅ Review complete! Use get_review_report to see findings."
    : "⏳ Review in progress..."
}
  `.trim();

  return {
    content: [
      {
        type: "text",
        text: statusText,
      },
    ],
  };
}

// Tool 3: Get review report
async function getReviewReport(args) {
  const { session_id, format } = args;

  const response = await callBridge(`/api/v1/review/${session_id}/report`);

  if (format === "json") {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(response, null, 2),
        },
      ],
    };
  }

  // Format as readable text
  const report = response.report;

  let reportText = `
# Code Review Report

**Session**: ${session_id}
**Overall Score**: ${report.overall_score}/100
**Quality Gate**: ${report.quality_gate}

## Summary

- Critical Issues: ${report.summary.critical}
- High Priority: ${report.summary.high}
- Medium Priority: ${report.summary.medium}
- Low Priority: ${report.summary.low}

## Priority Fixes

${report.priority_fixes
  .map(
    (fix, i) => `
${i + 1}. **${fix.issue}** (${fix.agent})
   - Severity: ${fix.severity}
   - Fix: ${fix.fix}
`
  )
  .join("\n")}

## Agent Findings

${report.agents
  .map(
    (agent) => `
### ${agent.name} (Score: ${agent.score}/100)

${agent.findings
  .map(
    (finding) => `
- **${finding.severity.toUpperCase()}**: ${finding.description}
  Location: ${finding.location || "N/A"}
  Fix: ${finding.fix || "N/A"}
`
  )
  .join("\n")}
`
  )
  .join("\n")}

## Recommendation

${report.recommendation}

${
  report.quality_gate === "passed"
    ? "✅ Code is ready for production"
    : "❌ Code needs fixes before deployment"
}
  `.trim();

  return {
    content: [
      {
        type: "text",
        text: reportText,
      },
    ],
  };
}

// Tool 4: Apply suggested fixes
async function applyFixes(args) {
  const { session_id, fix_priorities } = args;

  const response = await callBridge(`/api/v1/review/${session_id}/fix`, "POST", {
    fix_priorities: fix_priorities || ["critical", "high"],
  });

  return {
    content: [
      {
        type: "text",
        text: `
# Applied Fixes

**Fixes Applied**: ${response.fixes_applied}

## Fixed Code

\`\`\`${response.language}
${response.fixed_code}
\`\`\`

## Changes Made

${response.changes
  .map(
    (change, i) => `
${i + 1}. ${change.description}
   - File: ${change.file}
   - Lines: ${change.lines}
`
  )
  .join("\n")}

## Next Steps

${
  response.needs_review
    ? "⚠️  Some issues remain. Re-submit for review."
    : "✅ All critical issues fixed. Code is ready!"
}
        `.trim(),
      },
    ],
  };
}

// Tool 5: Quick security scan
async function quickSecurityScan(args) {
  const { code, language } = args;

  const response = await callBridge("/api/v1/scan/security", "POST", {
    code,
    language: language || "javascript",
  });

  const findings = response.findings;

  let scanText = `
# Security Scan Results

**Language**: ${language}
**Vulnerabilities Found**: ${findings.length}

${
  findings.length === 0
    ? "✅ No security vulnerabilities detected"
    : `
## Vulnerabilities

${findings
  .map(
    (finding, i) => `
${i + 1}. **${finding.type}** (${finding.severity})
   - Description: ${finding.description}
   - Location: ${finding.location}
   - Exploit: ${finding.exploit || "N/A"}
   - Fix: ${finding.fix}
`
  )
  .join("\n")}
`
}
  `.trim();

  return {
    content: [
      {
        type: "text",
        text: scanText,
      },
    ],
  };
}

// Tool 6: Generate tests
async function generateTests(args) {
  const { code, language, test_framework } = args;

  const response = await callBridge("/api/v1/generate/tests", "POST", {
    code,
    language: language || "javascript",
    test_framework: test_framework || "jest",
  });

  return {
    content: [
      {
        type: "text",
        text: `
# Generated Tests

**Test Framework**: ${test_framework || "jest"}
**Test Cases**: ${response.test_count}

\`\`\`${language}
${response.test_code}
\`\`\`

## Coverage

- Functions: ${response.coverage.functions}%
- Lines: ${response.coverage.lines}%
- Branches: ${response.coverage.branches}%

## Test Cases

${response.test_cases
  .map(
    (tc, i) => `
${i + 1}. ${tc.name}
   - Type: ${tc.type}
   - Description: ${tc.description}
`
  )
  .join("\n")}
        `.trim(),
      },
    ],
  };
}

// Register tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "submit_code_for_review",
        description:
          "Submit code to the Council agents for comprehensive review including security, QA, performance, and architecture analysis. Returns a session ID to track the review.",
        inputSchema: {
          type: "object",
          properties: {
            code: {
              type: "string",
              description: "The code to review",
            },
            language: {
              type: "string",
              description: "Programming language (e.g., javascript, python, go)",
              default: "javascript",
            },
            context: {
              type: "string",
              description: "Context about the code (e.g., 'Express API authentication')",
            },
            quality_gates: {
              type: "array",
              items: { type: "string" },
              description: "Quality gates to check (security, qa, performance, architecture)",
              default: ["security", "qa", "performance"],
            },
          },
          required: ["code"],
        },
      },
      {
        name: "get_review_status",
        description:
          "Check the status of an ongoing code review. Shows progress and which agents are currently analyzing.",
        inputSchema: {
          type: "object",
          properties: {
            session_id: {
              type: "string",
              description: "Session ID from submit_code_for_review",
            },
          },
          required: ["session_id"],
        },
      },
      {
        name: "get_review_report",
        description:
          "Get the detailed review report with findings from all agents, priority fixes, and recommendations.",
        inputSchema: {
          type: "object",
          properties: {
            session_id: {
              type: "string",
              description: "Session ID from submit_code_for_review",
            },
            format: {
              type: "string",
              enum: ["text", "json"],
              description: "Report format",
              default: "text",
            },
          },
          required: ["session_id"],
        },
      },
      {
        name: "apply_fixes",
        description:
          "Automatically apply suggested fixes from the review. Returns the fixed code with explanations of changes made.",
        inputSchema: {
          type: "object",
          properties: {
            session_id: {
              type: "string",
              description: "Session ID from submit_code_for_review",
            },
            fix_priorities: {
              type: "array",
              items: {
                type: "string",
                enum: ["critical", "high", "medium", "low"],
              },
              description: "Which severity levels to fix",
              default: ["critical", "high"],
            },
          },
          required: ["session_id"],
        },
      },
      {
        name: "quick_security_scan",
        description:
          "Run a quick security vulnerability scan on code without full review. Faster than full review for security-only checks.",
        inputSchema: {
          type: "object",
          properties: {
            code: {
              type: "string",
              description: "The code to scan",
            },
            language: {
              type: "string",
              description: "Programming language",
              default: "javascript",
            },
          },
          required: ["code"],
        },
      },
      {
        name: "generate_tests",
        description:
          "Generate comprehensive test cases for the provided code. Includes unit tests, edge cases, and integration tests.",
        inputSchema: {
          type: "object",
          properties: {
            code: {
              type: "string",
              description: "The code to generate tests for",
            },
            language: {
              type: "string",
              description: "Programming language",
              default: "javascript",
            },
            test_framework: {
              type: "string",
              description: "Test framework to use (jest, mocha, pytest, etc.)",
              default: "jest",
            },
          },
          required: ["code"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "submit_code_for_review":
        return await submitCodeForReview(args);
      case "get_review_status":
        return await getReviewStatus(args);
      case "get_review_report":
        return await getReviewReport(args);
      case "apply_fixes":
        return await applyFixes(args);
      case "quick_security_scan":
        return await quickSecurityScan(args);
      case "generate_tests":
        return await generateTests(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Code Quality Bridge MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
