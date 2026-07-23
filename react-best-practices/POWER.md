---
name: "react-best-practices"
displayName: "React Best Practices"
description: "React and Next.js performance optimization guidelines from Vercel Engineering. 45 rules across 8 categories, prioritized by impact from CRITICAL to LOW."
keywords: ["react", "nextjs", "performance", "optimization", "bundle", "waterfall", "re-render", "ssr", "vercel"]
author: "Vercel"
---

# React Best Practices

## Overview

Comprehensive performance optimization guide for React and Next.js applications, maintained by Vercel Engineering. Contains 45 rules across 8 categories, prioritized by impact to guide code review, refactoring, and code generation.

**Core Principle:** Performance work should start at the top of the stack. If a request waterfall adds 600ms of waiting time, optimizing `useMemo` calls won't help. Fix waterfalls first, then bundle size, then work down the priority list.

## When to Apply

Reference these guidelines when:
- Writing new React components or Next.js pages
- Implementing data fetching (client or server-side)
- Reviewing code for performance issues
- Refactoring existing React/Next.js code
- Optimizing bundle size or load times

## Rule Categories by Priority

| Priority | Category | Impact | Prefix | Rules |
|----------|----------|--------|--------|-------|
| 1 | Eliminating Waterfalls | CRITICAL | `async-` | 5 |
| 2 | Bundle Size Optimization | CRITICAL | `bundle-` | 5 |
| 3 | Server-Side Performance | HIGH | `server-` | 5 |
| 4 | Client-Side Data Fetching | MEDIUM-HIGH | `client-` | 2 |
| 5 | Re-render Optimization | MEDIUM | `rerender-` | 7 |
| 6 | Rendering Performance | MEDIUM | `rendering-` | 7 |
| 7 | JavaScript Performance | LOW-MEDIUM | `js-` | 12 |
| 8 | Advanced Patterns | LOW | `advanced-` | 2 |

## How to Use

Read individual rule files for detailed explanations and code examples:

```
steering/async-parallel.md
steering/bundle-barrel-imports.md
```

For the complete guide with all rules expanded: `steering/full-guide.md`

## Available Steering Files

Each rule is available as a separate steering file. Use `readSteering` with the rule name to get detailed explanations and code examples.

- **full-guide** - Complete compiled document with all 45 rules (2,200+ lines)

### 1. Eliminating Waterfalls (CRITICAL)

- **async-defer-await** - Move await into branches where actually used
- **async-parallel** - Use Promise.all() for independent operations
- **async-dependencies** - Use better-all for partial dependencies
- **async-api-routes** - Start promises early, await late in API routes
- **async-suspense-boundaries** - Use Suspense to stream content

### 2. Bundle Size Optimization (CRITICAL)

- **bundle-barrel-imports** - Import directly, avoid barrel files
- **bundle-dynamic-imports** - Use next/dynamic for heavy components
- **bundle-defer-third-party** - Load analytics/logging after hydration
- **bundle-conditional** - Load modules only when feature is activated
- **bundle-preload** - Preload on hover/focus for perceived speed

### 3. Server-Side Performance (HIGH)

- **server-cache-react** - Use React.cache() for per-request deduplication
- **server-cache-lru** - Use LRU cache for cross-request caching
- **server-serialization** - Minimize data passed to client components
- **server-parallel-fetching** - Restructure components to parallelize fetches
- **server-after-nonblocking** - Use after() for non-blocking operations

### 4. Client-Side Data Fetching (MEDIUM-HIGH)

- **client-swr-dedup** - Use SWR for automatic request deduplication
- **client-event-listeners** - Deduplicate global event listeners

### 5. Re-render Optimization (MEDIUM)

- **rerender-defer-reads** - Don't subscribe to state only used in callbacks
- **rerender-memo** - Extract expensive work into memoized components
- **rerender-dependencies** - Use primitive dependencies in effects
- **rerender-derived-state** - Subscribe to derived booleans, not raw values
- **rerender-functional-setstate** - Use functional setState for stable callbacks
- **rerender-lazy-state-init** - Pass function to useState for expensive values
- **rerender-transitions** - Use startTransition for non-urgent updates

### 6. Rendering Performance (MEDIUM)

- **rendering-animate-svg-wrapper** - Animate div wrapper, not SVG element
- **rendering-content-visibility** - Use content-visibility for long lists
- **rendering-hoist-jsx** - Extract static JSX outside components
- **rendering-svg-precision** - Reduce SVG coordinate precision
- **rendering-hydration-no-flicker** - Use inline script for client-only data
- **rendering-activity** - Use Activity component for show/hide
- **rendering-conditional-render** - Use ternary, not && for conditionals

### 7. JavaScript Performance (LOW-MEDIUM)

- **js-batch-dom-css** - Group CSS changes via classes or cssText
- **js-index-maps** - Build Map for repeated lookups
- **js-cache-property-access** - Cache object properties in loops
- **js-cache-function-results** - Cache function results in module-level Map
- **js-cache-storage** - Cache localStorage/sessionStorage reads
- **js-combine-iterations** - Combine multiple filter/map into one loop
- **js-length-check-first** - Check array length before expensive comparison
- **js-early-exit** - Return early from functions
- **js-hoist-regexp** - Hoist RegExp creation outside loops
- **js-min-max-loop** - Use loop for min/max instead of sort
- **js-set-map-lookups** - Use Set/Map for O(1) lookups
- **js-tosorted-immutable** - Use toSorted() for immutability

### 8. Advanced Patterns (LOW)

- **advanced-event-handler-refs** - Store event handlers in refs
- **advanced-use-latest** - useLatest for stable callback refs

## Best Practices

### ✅ Do:
- Start with CRITICAL rules (waterfalls, bundle size) before micro-optimizations
- Use `Promise.all()` for independent async operations
- Import directly from source files, not barrel files
- Use `next/dynamic` for heavy components not needed on initial render
- Use `React.cache()` for per-request deduplication on the server
- Use SWR for client-side data fetching with automatic deduplication

### ❌ Don't:
- Optimize `useMemo`/`useCallback` before fixing waterfalls
- Import from barrel files (`import { X } from 'library'`)
- Load analytics/tracking scripts before hydration
- Subscribe to entire objects when you only need a derived boolean
- Use `&&` for conditional rendering (use ternary instead)

## References

- [React Documentation](https://react.dev)
- [Next.js Documentation](https://nextjs.org)
- [SWR Documentation](https://swr.vercel.app)
- [How we optimized package imports in Next.js](https://vercel.com/blog/how-we-optimized-package-imports-in-next-js)
- [Source Repository](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices)

---

**License:** MIT  
**Original Author:** [@shuding](https://x.com/shuding) at Vercel
