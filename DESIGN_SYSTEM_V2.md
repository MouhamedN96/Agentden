# AgentDen v2.0 - Design System

## Research Findings

### Key Patterns from Dribbble & Modern Tools

**From Code Editors:**
1. **Dark navy/teal combination** (not generic purple) - sophisticated, professional
2. **File tree with icons** - visual hierarchy, easy scanning
3. **Tabbed interfaces** - multiple files/views without clutter
4. **Inline suggestions/autocomplete** - contextual help
5. **Minimap for code navigation** - spatial awareness

**From Warp Terminal:**
1. **Command blocks** - each command is a visual unit
2. **Inline autocomplete with descriptions** - helpful, not intrusive
3. **Cyan/teal accent** on dark navy - modern, technical feel
4. **Smart spacing** - breathing room between elements
5. **Context-aware suggestions** - AI-powered help

**From Developer Dashboards:**
1. **Pastel data visualizations** - soft, not harsh
2. **Card-based layouts** - modular, scannable
3. **Micro-interactions** - hover states, transitions
4. **Status indicators** - color-coded, instant understanding
5. **Clean typography** - readable, professional

## New Color System

### Primary Palette (Not Generic!)
```css
/* Base - Deep Navy (not black) */
--bg-primary: oklch(15% 0.02 240);
--bg-secondary: oklch(18% 0.02 240);
--bg-tertiary: oklch(22% 0.02 240);

/* Accent - Electric Cyan (signature color) */
--accent-primary: oklch(75% 0.15 195);
--accent-secondary: oklch(65% 0.12 195);
--accent-glow: oklch(75% 0.15 195 / 0.3);

/* Text */
--text-primary: oklch(95% 0.01 240);
--text-secondary: oklch(70% 0.02 240);
--text-muted: oklch(50% 0.02 240);

/* Semantic Colors */
--success: oklch(75% 0.15 150); /* Mint green */
--warning: oklch(75% 0.15 80);  /* Amber */
--error: oklch(65% 0.20 25);    /* Coral red */
--info: oklch(70% 0.12 260);    /* Soft purple */
```

### Agent-Specific Colors
```css
--agent-qa: oklch(70% 0.15 150);        /* Mint */
--agent-security: oklch(65% 0.18 25);   /* Coral */
--agent-performance: oklch(75% 0.15 80); /* Amber */
--agent-architecture: oklch(70% 0.12 260); /* Purple */
```

## Typography

### Font Stack
```css
--font-sans: 'Inter Variable', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
--font-display: 'Cal Sans', 'Inter Variable', sans-serif;
```

### Scale
```css
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
```

## Spacing System

```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-12: 3rem;    /* 48px */
--space-16: 4rem;    /* 64px */
```

## Manus-Style Execution Window

### Layout
```
┌─────────────────────────────────────────────────────────┐
│ Code Editor (60%)         │ Execution Window (40%)      │
│                            │                             │
│ Monaco Editor              │ ┌─ Agent Activity ─────┐   │
│ with syntax highlighting   │ │ ● QA Agent           │   │
│                            │ │   Analyzing code...  │   │
│                            │ │                      │   │
│                            │ │ ● Security Agent     │   │
│                            │ │   Scanning for...    │   │
│                            │ └─────────────────────┘   │
│                            │                             │
│                            │ ┌─ Sandbox Output ─────┐   │
│                            │ │ $ Running tests...   │   │
│                            │ │ ✓ 3/3 tests passed   │   │
│                            │ └─────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Features
1. **Resizable split panel** - drag to adjust
2. **Agent activity feed** - real-time updates with avatars
3. **Sandbox terminal output** - actual execution logs
4. **Collapsible sections** - hide what you don't need
5. **Status indicators** - pulsing dots for active agents
6. **Syntax-highlighted logs** - colored output
7. **Scroll to bottom** - auto-follow new logs

## Key Components

### 1. Command Block (Warp-inspired)
```
┌────────────────────────────────────────┐
│ > Submit for Review                    │
│   ┌────────────────────────────────┐   │
│   │ Your code will be analyzed by  │   │
│   │ 4 AI agents: QA, Security,     │   │
│   │ Performance, Architecture      │   │
│   └────────────────────────────────┘   │
│   [Submit] [Cancel]                    │
└────────────────────────────────────────┘
```

### 2. Agent Status Card
```
┌──────────────────────────────┐
│ ● Security Agent             │
│ ━━━━━━━━━━━━━━━━━━━━ 75%    │
│                              │
│ Found 2 vulnerabilities:     │
│ • SQL injection (line 42)    │
│ • XSS risk (line 89)         │
│                              │
│ [View Details]               │
└──────────────────────────────┘
```

### 3. Finding Card (Inline)
```
┌────────────────────────────────────────┐
│ ⚠ High Severity                        │
│ SQL Injection Vulnerability            │
│                                        │
│ Line 42: Direct string interpolation   │
│ in SQL query allows injection attacks  │
│                                        │
│ Suggested Fix:                         │
│ Use parameterized queries              │
│                                        │
│ [Apply Fix] [Ignore] [Learn More]     │
└────────────────────────────────────────┘
```

## Micro-Interactions

1. **Hover states** - subtle lift + glow
2. **Click feedback** - scale down slightly
3. **Loading states** - skeleton screens, not spinners
4. **Success animations** - checkmark draw-in
5. **Error shake** - gentle horizontal shake
6. **Transitions** - 200ms ease-out for most
7. **Stagger animations** - items appear in sequence

## Advanced Features

### 1. Split-Screen Diff View
- Side-by-side comparison
- Inline change highlighting
- Scroll synchronization
- Accept/reject changes

### 2. Inline Annotations
- Click line numbers to add notes
- Agent findings appear inline
- Collapsible annotation threads
- Markdown support in comments

### 3. Drag-and-Drop
- Drop files anywhere to upload
- Visual feedback during drag
- Multiple file support
- Progress indicators

### 4. Command Palette
- Cmd/Ctrl+K to open
- Fuzzy search
- Keyboard navigation
- Recent actions

## Mobile Adaptations

1. **Bottom sheet** for execution window
2. **Swipe gestures** - dismiss, navigate
3. **Touch-optimized** - larger hit areas
4. **Simplified layout** - single column on mobile
5. **Native-like animations** - spring physics

## Unique Visual Elements

1. **Glow effects** on active elements
2. **Gradient borders** on cards
3. **Animated grid background** - subtle movement
4. **Custom scrollbars** - styled to match theme
5. **Floating action button** - quick submit
6. **Toast notifications** - corner, auto-dismiss
7. **Confetti** on successful review

## Accessibility

1. **High contrast mode** - WCAG AAA
2. **Keyboard navigation** - all features
3. **Screen reader** - proper ARIA labels
4. **Focus indicators** - visible, not intrusive
5. **Reduced motion** - respect prefers-reduced-motion

## Performance Targets

- **First Contentful Paint**: < 1s
- **Time to Interactive**: < 2s
- **60fps animations** - no jank
- **Lazy load** - code editor, heavy components
- **Code splitting** - route-based

## Inspiration Sources

- **Warp Terminal**: Command blocks, autocomplete
- **Linear**: Clean, fast, keyboard-first
- **Vercel**: Deployment logs, status indicators
- **Raycast**: Command palette, shortcuts
- **Framer**: Smooth animations, polish
- **Arc Browser**: Unique visual language
- **21st.dev**: Modern developer aesthetic
