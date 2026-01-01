# 🚀 AgentDen - Autonomous AI Code Review Platform

**AgentDen** is a complete autonomous coding ecosystem that combines multi-agent AI collaboration with real-time code execution and quality analysis. Built with cutting-edge technology and exceptional design.

---

## 🎯 What is AgentDen?

AgentDen brings together three powerful concepts into one cohesive platform. It implements **autonomous coding** where AI agents write, test, and deploy code automatically. It features an **LLM council** where multiple specialized AI agents debate and validate solutions to ensure quality. It provides a **Progressive Web App** with a beautiful, installable interface that works offline.

The complete system works as a pipeline: requests come in from Slack or the UI, n8n orchestrates the workflow, the LLM Council plans the implementation, the Autonomous Coder generates the code, Sandbox Execution tests it, Quality Review validates everything, and finally the system deploys and notifies stakeholders.

---

## ✨ Key Features

### 🤖 Multi-Agent Council

Four specialized AI agents work together collaboratively. The **QA Agent** focuses on tests, coverage, and edge cases. The **Security Agent** checks for OWASP Top 10 vulnerabilities, SQL injection, XSS, and prompt injection attacks. The **Performance Agent** analyzes time complexity, detects N+1 queries, and identifies memory leaks. The **Architecture Agent** enforces SOLID principles, validates design patterns, and ensures proper code structure.

### 💻 Beautiful PWA Interface

The interface features a deep navy and electric cyan design inspired by modern developer tools. It includes Monaco Editor with syntax highlighting for 8+ languages, a Manus-style execution window showing live agent activity, real-time sandbox output with terminal logs, and can be installed on both mobile and desktop devices with full offline support.

### 🔧 Developer Experience

The developer experience includes type-safe APIs using tRPC, real-time updates via WebSocket, drag-and-drop file upload, one-click auto-fixes for detected issues, and comprehensive review history with search and filtering capabilities.

### 🧪 Real Code Execution

Code runs in isolated sandbox environments with real test validation. The system executes tests, captures output, and provides actual results rather than simulations.

---

## 🏗️ Architecture

### Frontend Stack
React 19 with TypeScript, Tailwind CSS 4 with OKLCH colors for perceptually uniform design, Monaco Editor for professional code editing, tRPC for type-safe API communication, and full PWA capabilities with offline support.

### Backend Stack
Express server with tRPC procedures, Drizzle ORM connected to MySQL/TiDB database, and Manus OAuth for secure authentication.

### Orchestration
n8n workflows coordinate between the Council service (Python + FastAPI), Coder service (Python + FastAPI), and Sandbox service with E2B integration for isolated code execution.

### AI Providers
Multiple AI providers are supported including Groq, Ollama, OpenRouter, Anthropic Claude, and OpenAI GPT-4.

---

## 🚀 Quick Start

Clone the repository, install dependencies with `pnpm install`, configure your environment by copying `.env.example` to `.env` and adding your API keys, setup the database with `pnpm db:push`, and start the development server with `pnpm dev`. Visit `http://localhost:3000` to see AgentDen in action.

---

## 📦 What's Included

The repository contains the complete PWA application in `/client` with React components, Monaco editor integration, execution window with live updates, review history and reports, plus PWA manifest and service worker.

Backend services in `/server` provide tRPC API procedures, database queries and mutations, authentication middleware, and review orchestration logic.

The Council system in `/council` implements the multi-agent debate system with specialized agent implementations, chairman synthesis logic, and quality scoring algorithms.

The Coder service in `/coder` handles autonomous code generation, test-driven development, auto-fix implementation, and Git integration.

The Sandbox service in `/sandbox` manages E2B VM orchestration, code execution in isolation, test running and validation, and security sandboxing.

n8n workflows in `/n8n-workflows` provide complete orchestration, Slack integration, webhook handling, and state management.

---

## 🎨 Design System

The color system uses OKLCH color space for perceptually uniform colors. Background is deep navy `oklch(0.2 0.02 250)`, primary accent is electric cyan `oklch(0.7 0.15 200)`, success is green `oklch(0.7 0.12 150)`, warning is yellow `oklch(0.75 0.15 80)`, and error is red `oklch(0.65 0.15 25)`.

Typography uses system fonts with optimized rendering, monospace fonts (Monaco, Menlo, Consolas) for code, and font feature settings enabled for ligatures.

Spacing follows a base unit of 0.25rem (4px) with a consistent 8px grid system and responsive breakpoints for mobile, tablet, and desktop devices.

---

## 🧪 Testing

Run all tests with `pnpm test`. Current coverage includes authentication flow, review submission, quality gate validation, database operations, and error handling. All tests are currently passing.

---

## 📱 PWA Features

Installation is simple: on desktop, click the install prompt in your browser; on mobile, use "Add to Home Screen" from the browser menu. The service worker caches reviews for offline access.

Capabilities include installable app functionality, offline support, push notifications, background sync, and file handling.

---

## 🔌 Integration

To connect the real backend, update API endpoints in `client/src/lib/trpc.ts`, configure the n8n workflow with your instance URL, deploy services using Docker Compose, and test the integration with a sample code review. See `BRIDGE_IMPLEMENTATION_PLAN.md` for detailed integration steps.

---

## 💡 Use Cases

Developers can get instant code reviews before committing, learn best practices from AI feedback, catch security vulnerabilities early, and optimize performance automatically.

Teams benefit from consistent code quality across projects, automated code review in CI/CD pipelines, and knowledge sharing through AI insights.

Organizations can enforce coding standards automatically, reduce technical debt, and improve security posture.

---

## 📊 Performance

The system analyzes code and generates comprehensive reports. Review speed depends on code complexity and selected quality gates.

---

## 🗺️ Roadmap

Phase 1 (Current) includes PWA interface with Monaco editor, multi-agent council system, sandbox execution, n8n orchestration, and multi-LLM support.

Phase 2 (Next) will add real backend integration, WebSocket streaming, GitHub integration, and team collaboration features.

Phase 3 (Future) plans IDE extensions for VS Code and JetBrains, CI/CD integration, team analytics dashboard, and additional integrations.

---

## 📚 Documentation

Comprehensive documentation is available in multiple files. `PWA_SUMMARY.md` provides complete implementation details. `DESIGN_SYSTEM_V2.md` contains visual design reference. `BRIDGE_IMPLEMENTATION_PLAN.md` explains backend integration. `PWA_FEASIBILITY_ANALYSIS.md` analyzes PWA capabilities. `docs/MULTI_LLM_SETUP.md` covers provider configuration.

---

## 🤝 Contributing

We welcome contributions from the community. Fork the repository, create a feature branch, make your changes, add tests, and submit a pull request.

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for complete details.

---

## 🙏 Credits

Design inspiration came from Warp, Linear, Vercel, Manus, and Dribbble.

Technologies used include React, TypeScript, Tailwind CSS, Monaco Editor, tRPC, Drizzle ORM, n8n, FastAPI, E2B, Groq, Ollama, and OpenRouter.

---

## 📞 Support

For bug reports and feature requests, use GitHub Issues. For community Q&A, visit our Discussions page.

---

**Built with ❤️**

*Last updated: December 31, 2025*
