---
name: "react-best-practices"
displayName: "React Best Practices"
description: "React and Next.js performance optimization guidelines from Vercel Engineering. Contains 45+ rules across 8 categories, prioritized by impact to guide code review, refactoring, and optimization."
keywords: ["react", "nextjs", "performance", "optimization", "vercel", "best-practices"]
author: "Vercel Engineering"
---

# React Best Practices

Comprehensive performance optimization guide for React and Next.js applications, maintained by Vercel Engineering. Contains 45+ rules across 8 categories, prioritized by impact from critical (eliminating waterfalls, reducing bundle size) to incremental (advanced patterns).

## Overview

This power provides detailed performance optimization guidelines for React and Next.js development. Each rule includes:
- Clear explanation of why it matters
- Incorrect code example with explanation
- Correct code example with explanation
- Impact metrics and priority levels
- Real-world context and references

## When to Use

Reference these guidelines when:
- Writing new React components or Next.js pages
- Implementing data fetching (client or server-side)
- Reviewing code for performance issues
- Refactoring existing React/Next.js code
- Optimizing bundle size or load times
- Conducting code reviews

## Rule Categories by Priority

| Priority | Category | Impact | Rules |
|----------|----------|--------|-------|
| 1 | Eliminating Waterfalls | CRITICAL | 5 rules |
| 2 | Bundle Size Optimization | CRITICAL | 5 rules |
| 3 | Server-Side Performance | HIGH | 5 rules |
| 4 | Client-Side Data Fetching | MEDIUM-HIGH | 2 rules |
| 5 | Re-render Optimization | MEDIUM | 7 rules |
| 6 | Rendering Performance | MEDIUM | 7 rules |
| 7 | JavaScript Performance | LOW-MEDIUM | 12 rules |
| 8 | Advanced Patterns | LOW | 2 rules |

## Quick Reference

### 1. Eliminating Waterfalls (CRITICAL)

Waterfalls are the #1 performance killer. Each sequential await adds full network latency. Eliminating them yields the largest gains (2-10× improvement).

- **async-defer-await** - Move await into branches where actually used
- **async-parallel** - Use Promise.all() for independent operations
- **async-dependencies** - Use better-all for partial dependencies
- **async-api-routes** - Start promises early, await late in API routes
- **async-suspense-boundaries** - Use Suspense to stream content

### 2. Bundle Size Optimization (CRITICAL)

Reducing initial bundle size improves Time to Interactive and Largest Contentful Paint (200-800ms savings).

- **bundle-barrel-imports** - Import directly, avoid barrel files
- **bundle-dynamic-imports** - Use next/dynamic for heavy components
- **bundle-defer-third-party** - Load analytics/logging after hydration
- **bundle-conditional** - Load modules only when feature is activated
- **bundle-preload** - Preload on hover/focus for perceived speed

### 3. Server-Side Performance (HIGH)

Optimizing server-side rendering and data fetching eliminates server-side waterfalls and reduces response times.

- **server-cache-react** - Use React.cache() for per-request deduplication
- **server-cache-lru** - Use LRU cache for cross-request caching
- **server-serialization** - Minimize data passed to client components
- **server-parallel-fetching** - Restructure components to parallelize fetches
- **server-after-nonblocking** - Use after() for non-blocking operations

### 4. Client-Side Data Fetching (MEDIUM-HIGH)

Automatic deduplication and efficient data fetching patterns reduce redundant network requests.

- **client-swr-dedup** - Use SWR for automatic request deduplication
- **client-event-listeners** - Deduplicate global event listeners

### 5. Re-render Optimization (MEDIUM)

Reducing unnecessary re-renders minimizes wasted computation and improves UI responsiveness.

- **rerender-defer-reads** - Don't subscribe to state only used in callbacks
- **rerender-memo** - Extract expensive work into memoized components
- **rerender-dependencies** - Use primitive dependencies in effects
- **rerender-derived-state** - Subscribe to derived booleans, not raw values
- **rerender-functional-setstate** - Use functional setState for stable callbacks
- **rerender-lazy-state-init** - Pass function to useState for expensive values
- **rerender-transitions** - Use startTransition for non-urgent updates

### 6. Rendering Performance (MEDIUM)

Optimizing the rendering process reduces the work the browser needs to do.

- **rendering-animate-svg-wrapper** - Animate div wrapper, not SVG element
- **rendering-content-visibility** - Use content-visibility for long lists
- **rendering-hoist-jsx** - Extract static JSX outside components
- **rendering-svg-precision** - Reduce SVG coordinate precision
- **rendering-hydration-no-flicker** - Use inline script for client-only data
- **rendering-activity** - Use Activity component for show/hide
- **rendering-conditional-render** - Use ternary, not && for conditionals

### 7. JavaScript Performance (LOW-MEDIUM)

Micro-optimizations for hot paths can add up to meaningful improvements.

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

Advanced patterns for specific cases that require careful implementation.

- **advanced-event-handler-refs** - Store event handlers in refs
- **advanced-use-latest** - useLatest for stable callback refs

## Available Steering Files

This power includes detailed steering files for each rule category. Use these for in-depth guidance on specific optimization areas:

- **eliminating-waterfalls.md** - Critical async optimization patterns
- **bundle-optimization.md** - Critical bundle size reduction techniques
- **server-performance.md** - High-impact server-side optimizations
- **client-data-fetching.md** - Client-side data fetching patterns
- **rerender-optimization.md** - Re-render reduction strategies
- **rendering-performance.md** - Browser rendering optimizations
- **javascript-performance.md** - JavaScript micro-optimizations
- **advanced-patterns.md** - Advanced React patterns

## Best Practices

1. **Prioritize by Impact** - Focus on CRITICAL and HIGH impact rules first
2. **Measure Before Optimizing** - Use profiling tools to identify actual bottlenecks
3. **Apply Incrementally** - Don't try to apply all rules at once
4. **Test Performance** - Verify improvements with real metrics
5. **Consider Trade-offs** - Some optimizations add complexity
6. **Stay Updated** - React and Next.js evolve; patterns may change

## Common Patterns

### Code Review Checklist

When reviewing React/Next.js code, check for:

1. **Waterfalls** - Are there sequential awaits that could be parallel?
2. **Barrel Imports** - Are components importing from barrel files?
3. **Bundle Size** - Are heavy libraries loaded upfront?
4. **Server Caching** - Is data being fetched multiple times?
5. **Re-renders** - Are components re-rendering unnecessarily?

### Refactoring Workflow

1. **Profile** - Use React DevTools Profiler and Chrome DevTools
2. **Identify** - Find the highest-impact issues
3. **Apply Rules** - Reference specific rules from this power
4. **Measure** - Verify the improvement
5. **Iterate** - Move to the next highest-impact issue

## References

- [React Documentation](https://react.dev)
- [Next.js Documentation](https://nextjs.org)
- [SWR Documentation](https://swr.vercel.app)
- [How we optimized package imports in Next.js](https://vercel.com/blog/how-we-optimized-package-imports-in-next-js)
- [How we made the Vercel dashboard twice as fast](https://vercel.com/blog/how-we-made-the-vercel-dashboard-twice-as-fast)

---

**Version:** 1.0.0  
**Source:** Vercel Engineering  
**License:** MIT
