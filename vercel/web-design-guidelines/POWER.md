---
name: "web-design-guidelines"
displayName: "Web Design Guidelines"
description: "Review UI code for compliance with web interface best practices. Audits code for 100+ rules covering accessibility, performance, UX, forms, animations, typography, images, navigation, dark mode, touch interactions, and internationalization."
keywords: ["web", "design", "accessibility", "ui", "ux", "a11y", "wcag", "performance", "best-practices"]
author: "Vercel"
---

# Web Design Guidelines

Comprehensive web interface guidelines for reviewing and auditing UI code. This power helps ensure your web applications follow best practices across accessibility, performance, user experience, and modern web standards.

## Overview

This power provides a structured approach to reviewing UI code against 100+ rules covering:

- **Accessibility** - ARIA labels, semantic HTML, keyboard navigation
- **Focus States** - Visible focus indicators, focus-visible patterns
- **Forms** - Autocomplete, validation, error handling
- **Animation** - Respecting user preferences, compositor-friendly transforms
- **Typography** - Proper characters, formatting, and readability
- **Images** - Dimensions, lazy loading, alt text
- **Performance** - Virtualization, layout optimization, preconnect
- **Navigation & State** - URL state management, deep-linking
- **Dark Mode & Theming** - Color schemes, theme preferences
- **Touch & Interaction** - Touch-action, tap highlights
- **Locale & i18n** - Internationalization APIs, formatting

## When to Use

Use this power when:
- Reviewing UI code for best practices
- Conducting accessibility audits
- Checking design implementation quality
- Performing code reviews on frontend code
- Ensuring WCAG compliance
- Optimizing user experience
- Preparing for production deployment

## How It Works

The guidelines are maintained in the official Vercel web-interface-guidelines repository and should be fetched fresh for each review to ensure you have the latest rules.

### Guidelines Source

The complete, up-to-date guidelines are available at:

```
https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
```

### Review Process

1. **Fetch Latest Guidelines** - Always fetch the current version from the source URL above
2. **Identify Files to Review** - Determine which files need auditing (components, pages, styles)
3. **Apply All Rules** - Check code against all rules in the fetched guidelines
4. **Report Findings** - Output issues in a clear, actionable format

## Usage Examples

### Example 1: Review a Component

```
"Review my Button component for accessibility and best practices"

Steps:
1. Fetch guidelines from source URL
2. Read the Button component file
3. Check against all applicable rules
4. Report findings with file:line references
```

### Example 2: Audit Entire UI

```
"Check my UI against web design best practices"

Steps:
1. Fetch guidelines from source URL
2. Ask user which files/patterns to review
3. Read specified files
4. Apply all rules from guidelines
5. Output comprehensive findings
```

### Example 3: Accessibility Check

```
"Audit my form for accessibility issues"

Steps:
1. Fetch guidelines from source URL
2. Read form component files
3. Focus on accessibility, forms, and keyboard navigation rules
4. Report accessibility violations
```

## Rule Categories

### 1. Accessibility (ARIA, Semantic HTML, Keyboard)

Ensures your UI is usable by everyone, including people using assistive technologies.

**Key areas:**
- Proper ARIA labels and roles
- Semantic HTML elements
- Keyboard navigation support
- Screen reader compatibility
- Focus management

### 2. Focus States

Visible focus indicators are critical for keyboard navigation and accessibility.

**Key areas:**
- Visible focus indicators
- :focus-visible patterns
- Focus trap management
- Tab order optimization

### 3. Forms

Well-designed forms improve user experience and conversion rates.

**Key areas:**
- Autocomplete attributes
- Validation patterns
- Error handling and messaging
- Label associations
- Input types

### 4. Animation

Animations should enhance UX without causing motion sickness or performance issues.

**Key areas:**
- prefers-reduced-motion support
- Compositor-friendly transforms
- Animation performance
- Transition timing

### 5. Typography

Proper typography improves readability and professionalism.

**Key areas:**
- Curly quotes and apostrophes
- Proper ellipsis characters
- Tabular numbers for data
- Font loading strategies
- Line height and spacing

### 6. Images

Optimized images improve performance and accessibility.

**Key areas:**
- Width and height attributes
- Lazy loading
- Alt text
- Responsive images
- Image formats

### 7. Performance

Performance optimizations ensure fast, responsive interfaces.

**Key areas:**
- Virtual scrolling for long lists
- Layout thrashing prevention
- Preconnect for external resources
- Code splitting
- Resource hints

### 8. Navigation & State

URL state management enables sharing and bookmarking.

**Key areas:**
- URL reflects application state
- Deep-linking support
- Browser history management
- Navigation patterns

### 9. Dark Mode & Theming

Proper theme support respects user preferences.

**Key areas:**
- color-scheme meta tag
- theme-color meta tag
- CSS custom properties
- System preference detection
- Theme persistence

### 10. Touch & Interaction

Mobile-friendly interactions improve usability on touch devices.

**Key areas:**
- touch-action properties
- Tap highlight customization
- Touch target sizes
- Gesture support

### 11. Locale & Internationalization

Proper i18n ensures your app works globally.

**Key areas:**
- Intl.DateTimeFormat for dates
- Intl.NumberFormat for numbers
- Intl.ListFormat for lists
- Locale-aware sorting
- RTL support

## Best Practices

### Before Reviewing

1. **Fetch Latest Guidelines** - Always get the current version
2. **Understand Context** - Know what type of UI you're reviewing
3. **Prioritize Issues** - Focus on accessibility and critical UX issues first

### During Review

1. **Be Thorough** - Check all applicable rules
2. **Provide Context** - Explain why each issue matters
3. **Suggest Fixes** - Offer concrete solutions
4. **Reference Standards** - Link to WCAG, MDN, or other authoritative sources

### After Review

1. **Prioritize Fixes** - Categorize by severity (critical, high, medium, low)
2. **Track Progress** - Monitor which issues have been addressed
3. **Re-review** - Verify fixes after implementation

## Common Issues

### Accessibility Violations

- Missing alt text on images
- Buttons without accessible labels
- Poor color contrast
- Missing keyboard navigation
- Improper ARIA usage

### Performance Problems

- Missing image dimensions (causes layout shift)
- No lazy loading for below-fold images
- Layout thrashing from repeated DOM reads/writes
- Missing resource hints for external resources

### UX Issues

- No visible focus indicators
- Forms without autocomplete
- Poor error messages
- State not reflected in URL
- No dark mode support

## Integration with Development Workflow

### Code Review Checklist

Include these checks in your code review process:

- [ ] Accessibility: All interactive elements have labels
- [ ] Accessibility: Keyboard navigation works
- [ ] Focus: Visible focus indicators present
- [ ] Forms: Autocomplete attributes set
- [ ] Images: Width/height specified, alt text present
- [ ] Performance: Images lazy loaded where appropriate
- [ ] Animation: prefers-reduced-motion respected
- [ ] State: Important state reflected in URL
- [ ] Theme: Dark mode supported
- [ ] i18n: Dates/numbers formatted with Intl APIs

### Automated Checks

Consider integrating automated accessibility testing:

- axe-core for accessibility violations
- Lighthouse for performance and best practices
- ESLint plugins for React/JSX best practices

## References

- [Web Interface Guidelines Repository](https://github.com/vercel-labs/web-interface-guidelines)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN Web Docs](https://developer.mozilla.org/)
- [A11y Project](https://www.a11yproject.com/)
- [WebAIM](https://webaim.org/)

## Troubleshooting

### Issue: Guidelines URL not accessible

**Solution:** Check your internet connection and verify the URL is correct. The guidelines are hosted on GitHub and should be publicly accessible.

### Issue: Too many findings to review

**Solution:** Start with critical issues (accessibility, major UX problems) and work through them incrementally. Not all issues need to be fixed immediately.

### Issue: Conflicting recommendations

**Solution:** When guidelines conflict with project requirements, document the decision and reasoning. Accessibility should rarely be compromised.

---

**Version:** 1.0.0  
**Source:** Vercel  
**License:** MIT  
**Guidelines URL:** https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
