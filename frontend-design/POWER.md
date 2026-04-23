---
name: "frontend-design"
displayName: "Frontend Design"
description: "Create distinctive, production-grade frontend interfaces that avoid generic AI aesthetics. Guides bold design choices with memorable typography, color, and motion."
keywords: ["frontend", "design", "ui", "css", "aesthetics", "web", "react", "tailwind"]
author: "AWS"
---

# Frontend Design

## Overview

This power guides the creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. When building web components, pages, or applications, use this guidance to implement real working code with exceptional attention to aesthetic details and creative choices.

The goal is to create interfaces that are:
- **Visually striking and memorable** - Not another purple gradient on white
- **Production-grade and functional** - Real code, not mockups
- **Cohesive with clear aesthetic direction** - Intentional design choices
- **Meticulously refined** - Every detail matters

## Design Thinking Process

Before coding, understand the context and commit to a **BOLD** aesthetic direction:

### 1. Purpose
What problem does this interface solve? Who uses it?

### 2. Tone
Pick an extreme aesthetic direction. There are many flavors to choose from:
- Brutally minimal
- Maximalist chaos
- Retro-futuristic
- Organic/natural
- Luxury/refined
- Playful/toy-like
- Editorial/magazine
- Brutalist/raw
- Art deco/geometric
- Soft/pastel
- Industrial/utilitarian

Use these for inspiration but design one that is true to the aesthetic direction.

### 3. Constraints
Technical requirements: framework, performance, accessibility.

### 4. Differentiation
What makes this **UNFORGETTABLE**? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is **intentionality**, not intensity.

## Frontend Aesthetics Guidelines

### Typography

Choose fonts that are **beautiful, unique, and interesting**.

**AVOID:**
- Generic fonts: Arial, Inter, Roboto, system fonts
- Safe, predictable choices

**DO:**
- Opt for distinctive choices that elevate the frontend's aesthetics
- Unexpected, characterful font choices
- Pair a distinctive display font with a refined body font

### Color & Theme

Commit to a **cohesive aesthetic**.

**Best Practices:**
- Use CSS variables for consistency
- Dominant colors with sharp accents outperform timid, evenly-distributed palettes
- Avoid cliched color schemes (particularly purple gradients on white backgrounds)

### Motion & Animation

Use animations for effects and micro-interactions.

**Approach:**
- Prioritize CSS-only solutions for HTML
- Use Motion library for React when available
- Focus on high-impact moments: one well-orchestrated page load with staggered reveals (`animation-delay`) creates more delight than scattered micro-interactions
- Use scroll-triggering and hover states that surprise

### Spatial Composition

Break free from predictable layouts:
- Unexpected layouts
- Asymmetry
- Overlap
- Diagonal flow
- Grid-breaking elements
- Generous negative space OR controlled density

### Backgrounds & Visual Details

Create atmosphere and depth rather than defaulting to solid colors.

**Techniques:**
- Gradient meshes
- Noise textures
- Geometric patterns
- Layered transparencies
- Dramatic shadows
- Decorative borders
- Custom cursors
- Grain overlays

## What to NEVER Do

**NEVER use generic AI-generated aesthetics:**

| Category | Avoid |
|----------|-------|
| Typography | Inter, Roboto, Arial, system fonts |
| Colors | Purple gradients on white backgrounds |
| Layouts | Predictable component patterns |
| Overall | Cookie-cutter design lacking context-specific character |

## Implementation Guidance

### Match Complexity to Vision

- **Maximalist designs** need elaborate code with extensive animations and effects
- **Minimalist/refined designs** need restraint, precision, and careful attention to spacing, typography, and subtle details

Elegance comes from executing the vision well.

### Variety is Essential

- Vary between light and dark themes
- Use different fonts across projects
- Explore different aesthetics
- **NEVER** converge on common choices (e.g., Space Grotesk) across generations

### Code Quality

Implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Example Prompts

Use this power when asked to:

```
"Create a dashboard for a music streaming app"
"Build a landing page for an AI security startup"
"Design a settings panel with dark mode"
"Build a pixel art character store"
"Create a retro arcade-themed checkout flow"
```

The agent will choose a clear aesthetic direction and implement production code with meticulous attention to detail.

## Best Practices Summary

1. **Commit to a direction** - Don't hedge with generic components
2. **Be intentional** - Every choice should serve the aesthetic
3. **Surprise and delight** - Add unexpected details
4. **Execute with precision** - Details matter
5. **Avoid the median** - If it looks like every other AI-generated UI, start over

Remember: Extraordinary creative work is possible. Don't hold back - show what can truly be created when thinking outside the box and committing fully to a distinctive vision.

## Learn More

See the [Frontend Aesthetics Cookbook](https://github.com/anthropics/claude-cookbooks/blob/main/coding/prompting_for_frontend_aesthetics.ipynb) for detailed guidance on prompting for high-quality frontend design.

## Attribution

This power is inspired by and builds upon concepts from the [Frontend Aesthetics Cookbook](https://github.com/anthropics/claude-cookbooks/blob/main/coding/prompting_for_frontend_aesthetics.ipynb) by Anthropic, which is licensed under the MIT License.

---

**License:** MIT
