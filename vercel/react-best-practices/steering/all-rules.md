# All React Best Practices Rules

This file contains all 45+ performance optimization rules organized by category. Each rule includes detailed explanations, code examples, and impact metrics.

For individual rule files, see the `rules/` subdirectory.

## Table of Contents

1. [Eliminating Waterfalls (CRITICAL)](#1-eliminating-waterfalls-critical)
2. [Bundle Size Optimization (CRITICAL)](#2-bundle-size-optimization-critical)
3. [Server-Side Performance (HIGH)](#3-server-side-performance-high)
4. [Client-Side Data Fetching (MEDIUM-HIGH)](#4-client-side-data-fetching-medium-high)
5. [Re-render Optimization (MEDIUM)](#5-re-render-optimization-medium)
6. [Rendering Performance (MEDIUM)](#6-rendering-performance-medium)
7. [JavaScript Performance (LOW-MEDIUM)](#7-javascript-performance-low-medium)
8. [Advanced Patterns (LOW)](#8-advanced-patterns-low)

---

## 1. Eliminating Waterfalls (CRITICAL)

**Impact:** CRITICAL  
**Description:** Waterfalls are the #1 performance killer. Each sequential await adds full network latency. Eliminating them yields the largest gains.

### Rules in this category:

- async-defer-await
- async-parallel
- async-dependencies
- async-api-routes
- async-suspense-boundaries

**For detailed examples of each rule, see the individual files in `rules/async-*.md`**

---

## 2. Bundle Size Optimization (CRITICAL)

**Impact:** CRITICAL  
**Description:** Reducing initial bundle size improves Time to Interactive and Largest Contentful Paint.

### Rules in this category:

- bundle-barrel-imports
- bundle-dynamic-imports
- bundle-defer-third-party
- bundle-conditional
- bundle-preload

**For detailed examples of each rule, see the individual files in `rules/bundle-*.md`**

---

## 3. Server-Side Performance (HIGH)

**Impact:** HIGH  
**Description:** Optimizing server-side rendering and data fetching eliminates server-side waterfalls and reduces response times.

### Rules in this category:

- server-cache-react
- server-cache-lru
- server-serialization
- server-parallel-fetching
- server-after-nonblocking

**For detailed examples of each rule, see the individual files in `rules/server-*.md`**

---

## 4. Client-Side Data Fetching (MEDIUM-HIGH)

**Impact:** MEDIUM-HIGH  
**Description:** Automatic deduplication and efficient data fetching patterns reduce redundant network requests.

### Rules in this category:

- client-swr-dedup
- client-event-listeners

**For detailed examples of each rule, see the individual files in `rules/client-*.md`**

---

## 5. Re-render Optimization (MEDIUM)

**Impact:** MEDIUM  
**Description:** Reducing unnecessary re-renders minimizes wasted computation and improves UI responsiveness.

### Rules in this category:

- rerender-defer-reads
- rerender-memo
- rerender-dependencies
- rerender-derived-state
- rerender-functional-setstate
- rerender-lazy-state-init
- rerender-transitions

**For detailed examples of each rule, see the individual files in `rules/rerender-*.md`**

---

## 6. Rendering Performance (MEDIUM)

**Impact:** MEDIUM  
**Description:** Optimizing the rendering process reduces the work the browser needs to do.

### Rules in this category:

- rendering-animate-svg-wrapper
- rendering-content-visibility
- rendering-hoist-jsx
- rendering-svg-precision
- rendering-hydration-no-flicker
- rendering-activity
- rendering-conditional-render

**For detailed examples of each rule, see the individual files in `rules/rendering-*.md`**

---

## 7. JavaScript Performance (LOW-MEDIUM)

**Impact:** LOW-MEDIUM  
**Description:** Micro-optimizations for hot paths can add up to meaningful improvements.

### Rules in this category:

- js-batch-dom-css
- js-index-maps
- js-cache-property-access
- js-cache-function-results
- js-cache-storage
- js-combine-iterations
- js-length-check-first
- js-early-exit
- js-hoist-regexp
- js-min-max-loop
- js-set-map-lookups
- js-tosorted-immutable

**For detailed examples of each rule, see the individual files in `rules/js-*.md`**

---

## 8. Advanced Patterns (LOW)

**Impact:** LOW  
**Description:** Advanced patterns for specific cases that require careful implementation.

### Rules in this category:

- advanced-event-handler-refs
- advanced-use-latest

**For detailed examples of each rule, see the individual files in `rules/advanced-*.md`**

---

## How to Use These Rules

1. **Start with CRITICAL impact rules** - Focus on eliminating waterfalls and reducing bundle size first
2. **Profile before optimizing** - Use React DevTools and Chrome DevTools to identify actual bottlenecks
3. **Apply rules incrementally** - Don't try to apply everything at once
4. **Measure improvements** - Verify that optimizations actually help
5. **Consider trade-offs** - Some optimizations add code complexity

## References

- React Documentation: https://react.dev
- Next.js Documentation: https://nextjs.org
- SWR Documentation: https://swr.vercel.app
- Vercel Blog: https://vercel.com/blog
