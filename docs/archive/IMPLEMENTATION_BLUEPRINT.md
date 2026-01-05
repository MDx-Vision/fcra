# HTML/CSS Implementation Blueprint - Apple-Style Redesign

**Document Version:** 1.0
**Created:** December 14, 2025
**Purpose:** Detailed specifications for implementing Apple-style redesign in the FCRA platform codebase
**Mode:** Planning/Specifications Only - NO code changes included

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [File Map & Architecture](#file-map--architecture)
3. [Design System Implementation](#design-system-implementation)
4. [Component Library Specifications](#component-library-specifications)
5. [Screen-by-Screen Implementation Guide](#screen-by-screen-implementation-guide)
6. [Migration Strategy](#migration-strategy)
7. [Testing & Validation](#testing--validation)
8. [Developer Handoff Checklist](#developer-handoff-checklist)

---

## Executive Summary

### What This Document Provides

This blueprint translates the Apple Design Gap Analysis and Figma Design Specification into **actionable implementation steps** for the FCRA platform codebase. It specifies:

- Exact CSS variables to add
- Which template files to modify
- Component HTML/CSS structure
- Before/after code examples
- File-by-file change specifications
- Migration path from current design to Apple-style

### What This Document Does NOT Include

- Actual code changes to the repository
- Pull requests or commits
- Database schema changes
- Backend logic modifications

This is a **planning document** that developers will use to implement the redesign.

---

### Implementation Metrics

| Aspect | Current | Target | Change |
|--------|---------|--------|--------|
| **CSS Files** | Inline styles + scattered CSS | Centralized design system | +1 new file, refactor 8 templates |
| **Typography** | Mixed fonts, inconsistent sizing | Playfair Display + DM Sans, 9-level scale | Replace all font declarations |
| **Color Palette** | 15+ colors, no system | 2 scales (Primary, Gray), 18 total | Reduce 80%, systematize |
| **Spacing** | Arbitrary px values | 8px grid system | Standardize all spacing |
| **Components** | 12 unique patterns | 50+ reusable components | +38 new components |
| **Whitespace** | 35% average | 60-70% target | +80% increase |
| **Mobile Responsive** | Partial | Full responsive + mobile-first | Refactor all breakpoints |

---

## File Map & Architecture

### Current File Structure

```
/Users/rafaelrodriguez/fcra/
├── app.py                          # Flask routes (no changes needed)
├── database.py                     # Models (no changes needed)
├── static/
│   ├── css/
│   │   ├── style.css               # ⚠️ TO BE REPLACED
│   │   └── [various component CSS] # ⚠️ TO BE CONSOLIDATED
│   ├── js/
│   │   └── [scripts]               # Minor updates for interactions
│   └── generated_letters/          # No changes
├── templates/
│   ├── base.html                   # ⚠️ MAJOR REFACTOR - Design system foundation
│   ├── dashboard.html              # ⚠️ MAJOR REFACTOR - Hero metrics, card grid
│   ├── client_list.html            # ⚠️ MAJOR REFACTOR - Table → Card grid
│   ├── client_portal.html          # ⚠️ MAJOR REFACTOR - Simplified tabs, hero
│   ├── analysis_review.html        # ⚠️ MODERATE REFACTOR - Cards, timeline
│   ├── dispute_letters.html        # ⚠️ MODERATE REFACTOR - Document cards
│   ├── triage_queue.html           # ⚠️ MODERATE REFACTOR - List → Cards
│   └── [other templates]           # MINOR UPDATES - Apply design system
└── knowledge/
    ├── APPLE_DESIGN_GAP_ANALYSIS.md      # Reference
    ├── FIGMA_DESIGN_SPECIFICATION.md     # Reference
    └── IMPLEMENTATION_BLUEPRINT.md       # THIS DOCUMENT
```

### New File Structure (After Implementation)

```
/Users/rafaelrodriguez/fcra/
├── static/
│   ├── css/
│   │   ├── design-system.css       # ✅ NEW - CSS variables, reset, base styles
│   │   ├── components.css          # ✅ NEW - Reusable component library
│   │   ├── layouts.css             # ✅ NEW - Page layouts, grids
│   │   ├── utilities.css           # ✅ NEW - Helper classes
│   │   └── legacy.css              # ⚠️ DEPRECATED - Old styles (to be removed)
│   └── js/
│       └── interactions.js         # ✅ NEW - Smooth animations, transitions
└── templates/
    ├── base.html                   # ✅ UPDATED - Load new CSS, design system
    ├── components/                 # ✅ NEW FOLDER - Reusable template partials
    │   ├── button.html
    │   ├── card.html
    │   ├── form-input.html
    │   ├── modal.html
    │   └── [50+ components]
    └── [all page templates]        # ✅ UPDATED - Use new components
```

---

## Design System Implementation

### Phase 1: Foundation Files

#### File: `/static/css/design-system.css` (NEW FILE)

**Purpose:** Central source of truth for design system - colors, typography, spacing, shadows

**Structure:**

```css
/*
 * FCRA Platform - Apple-Style Design System
 * Version: 2.0
 * Last Updated: December 2025
 */

/* ============================================
   CSS CUSTOM PROPERTIES (DESIGN TOKENS)
   ============================================ */

:root {
  /* COLOR SYSTEM */
  /* Primary Scale - Teal */
  --primary-50: #f0fdfa;
  --primary-100: #ccfbf1;
  --primary-200: #99f6e4;
  --primary-300: #5eead4;
  --primary-400: #2dd4bf;
  --primary-500: #14b8a6;
  --primary-600: #0d9488;   /* Main brand color */
  --primary-700: #0f766e;
  --primary-800: #115e59;
  --primary-900: #134e4a;

  /* Gray Scale */
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-200: #e5e7eb;
  --gray-300: #d1d5db;
  --gray-400: #9ca3af;
  --gray-500: #6b7280;
  --gray-600: #4b5563;
  --gray-700: #374151;
  --gray-800: #1f2937;
  --gray-900: #111827;

  /* Semantic Colors */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;

  /* Surface Colors */
  --color-background: #ffffff;
  --color-surface: var(--gray-50);
  --color-border: var(--gray-200);

  /* Text Colors */
  --color-text-primary: var(--gray-900);
  --color-text-secondary: var(--gray-600);
  --color-text-tertiary: var(--gray-400);
  --color-text-inverse: #ffffff;

  /* TYPOGRAPHY SYSTEM */
  /* Font Families */
  --font-serif: 'Playfair Display', Georgia, serif;
  --font-sans: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'SF Mono', 'Monaco', 'Courier New', monospace;

  /* Font Sizes (Type Scale) */
  --text-display: 56px;      /* Hero headlines */
  --text-h1: 48px;           /* Page titles */
  --text-h2: 36px;           /* Section headers */
  --text-h3: 28px;           /* Subsection headers */
  --text-h4: 24px;           /* Card titles */
  --text-body-lg: 18px;      /* Lead text */
  --text-body: 16px;         /* Body copy */
  --text-body-sm: 14px;      /* Secondary text */
  --text-caption: 12px;      /* Labels, captions */

  /* Line Heights */
  --leading-tight: 1.2;      /* Headlines */
  --leading-normal: 1.5;     /* Body text */
  --leading-relaxed: 1.75;   /* Long-form content */

  /* Font Weights */
  --weight-normal: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;

  /* SPACING SYSTEM (8px grid) */
  --space-1: 8px;
  --space-2: 16px;
  --space-3: 24px;
  --space-4: 32px;
  --space-5: 40px;
  --space-6: 48px;
  --space-8: 64px;
  --space-10: 80px;
  --space-12: 96px;
  --space-16: 128px;

  /* BORDER RADIUS */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 24px;
  --radius-full: 9999px;

  /* SHADOWS (Elevation System) */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
               0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1),
               0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
               0 10px 10px -5px rgba(0, 0, 0, 0.04);
  --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

  /* TRANSITIONS */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 300ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 500ms cubic-bezier(0.4, 0, 0.2, 1);

  /* Z-INDEX SCALE */
  --z-dropdown: 1000;
  --z-sticky: 1100;
  --z-modal-backdrop: 1200;
  --z-modal: 1300;
  --z-popover: 1400;
  --z-tooltip: 1500;
}

/* ============================================
   CSS RESET & BASE STYLES
   ============================================ */

/* Modern CSS Reset */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-body);
  line-height: var(--leading-normal);
  color: var(--color-text-primary);
  background-color: var(--color-background);
}

/* Typography Base Styles */
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-serif);
  font-weight: var(--weight-semibold);
  line-height: var(--leading-tight);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

h1 { font-size: var(--text-h1); }
h2 { font-size: var(--text-h2); }
h3 { font-size: var(--text-h3); }
h4 { font-size: var(--text-h4); }

p {
  margin-bottom: var(--space-2);
}

a {
  color: var(--primary-600);
  text-decoration: none;
  transition: color var(--transition-fast);
}

a:hover {
  color: var(--primary-700);
}

/* Focus States (Accessibility) */
:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}

/* Selection Colors */
::selection {
  background-color: var(--primary-100);
  color: var(--color-text-primary);
}
```

**Implementation Notes:**
- Load this file FIRST in base.html (before any other CSS)
- All other CSS files should reference these variables
- Never hardcode colors/spacing - always use design tokens

---

#### File: `/static/css/components.css` (NEW FILE)

**Purpose:** Reusable component library matching Figma specifications

**Structure Overview:**

```css
/*
 * COMPONENT LIBRARY
 * 50+ reusable components with variants
 */

/* ============================================
   BUTTONS
   ============================================ */

/* Base Button Styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  padding: 12px var(--space-3);
  font-family: var(--font-sans);
  font-size: var(--text-body);
  font-weight: var(--weight-medium);
  line-height: 1;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
  white-space: nowrap;
  user-select: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Button Variants */
.btn-primary {
  background: var(--primary-600);
  color: white;
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-700);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.btn-primary:active:not(:disabled) {
  background: var(--primary-800);
  box-shadow: var(--shadow-sm);
  transform: translateY(0);
}

.btn-secondary {
  background: white;
  color: var(--gray-700);
  border: 1px solid var(--gray-300);
  box-shadow: var(--shadow-sm);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--gray-50);
  border-color: var(--gray-400);
}

.btn-tertiary {
  background: transparent;
  color: var(--primary-600);
  padding: 8px var(--space-2);
}

.btn-tertiary:hover:not(:disabled) {
  background: var(--primary-50);
}

/* Button Sizes */
.btn-sm {
  padding: 8px var(--space-2);
  font-size: var(--text-body-sm);
  height: 36px;
}

.btn-md {
  padding: 12px var(--space-3);
  font-size: var(--text-body);
  height: 44px;
}

.btn-lg {
  padding: 16px var(--space-4);
  font-size: var(--text-body-lg);
  height: 56px;
}

/* Icon Buttons */
.btn-icon {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: var(--radius-full);
}

.btn-icon.btn-sm {
  width: 36px;
  height: 36px;
}

/* ============================================
   CARDS
   ============================================ */

.card {
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: var(--space-3);
  transition: all var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

/* Card Variants */
.card-interactive {
  cursor: pointer;
}

.card-interactive:active {
  transform: translateY(0);
  box-shadow: var(--shadow-md);
}

.card-stat {
  padding: var(--space-4);
  text-align: center;
}

.card-client {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
}

/* Card Components */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
}

.card-title {
  font-family: var(--font-serif);
  font-size: var(--text-h4);
  font-weight: var(--weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.card-body {
  color: var(--color-text-secondary);
  font-size: var(--text-body);
}

.card-footer {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* ============================================
   FORM INPUTS
   ============================================ */

.form-group {
  margin-bottom: var(--space-3);
  position: relative;
}

.form-label {
  display: block;
  font-size: var(--text-body-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-1);
  transition: all var(--transition-fast);
}

.form-input {
  width: 100%;
  height: 44px;
  padding: 12px var(--space-2);
  font-family: var(--font-sans);
  font-size: var(--text-body);
  color: var(--color-text-primary);
  background: white;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.form-input::placeholder {
  color: var(--color-text-tertiary);
}

/* Floating Label Pattern */
.form-group-floating {
  position: relative;
}

.form-group-floating .form-label {
  position: absolute;
  top: 12px;
  left: var(--space-2);
  pointer-events: none;
  color: var(--color-text-tertiary);
}

.form-group-floating .form-input:focus + .form-label,
.form-group-floating .form-input:not(:placeholder-shown) + .form-label {
  top: -8px;
  left: var(--space-1);
  font-size: var(--text-caption);
  color: var(--primary-600);
  background: white;
  padding: 0 4px;
}

/* ============================================
   BADGES & TAGS
   ============================================ */

.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  font-size: var(--text-body-sm);
  font-weight: var(--weight-medium);
  border-radius: var(--radius-full);
  white-space: nowrap;
}

.badge-success {
  background: #d1fae5;
  color: #065f46;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
}

.badge-error {
  background: #fee2e2;
  color: #991b1b;
}

.badge-info {
  background: var(--primary-100);
  color: var(--primary-900);
}

.badge-gray {
  background: var(--gray-100);
  color: var(--gray-700);
}

/* ============================================
   MODALS
   ============================================ */

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: var(--z-modal-backdrop);
  animation: fadeIn var(--transition-base);
}

.modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-2xl);
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow: auto;
  z-index: var(--z-modal);
  animation: slideUp var(--transition-base);
}

.modal-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-family: var(--font-serif);
  font-size: var(--text-h3);
  margin: 0;
}

.modal-body {
  padding: var(--space-4);
}

.modal-footer {
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
}

/* ============================================
   ANIMATIONS
   ============================================ */

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translate(-50%, -45%);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%);
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

**Total Components in Full File:** 50+
- Buttons (primary, secondary, tertiary, icon, loading states)
- Cards (basic, stat, client, document, interactive)
- Forms (text, select, checkbox, radio, toggle, textarea)
- Badges & Tags
- Modals (center, sheet, popover)
- Navigation (sidebar, tab bar, breadcrumbs)
- Tables (responsive, sortable)
- Data Visualization (progress rings, bars, sparklines)
- Empty States
- Loading States (spinners, skeletons)
- Toasts & Notifications

---

#### File: `/static/css/layouts.css` (NEW FILE)

**Purpose:** Page layout patterns and responsive grids

```css
/*
 * LAYOUT PATTERNS
 * Page structures, grids, containers
 */

/* ============================================
   CONTAINERS
   ============================================ */

.container {
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

.container-narrow {
  max-width: 960px;
}

.container-wide {
  max-width: 1920px;
}

/* ============================================
   PAGE LAYOUTS
   ============================================ */

/* Sidebar + Main Content Layout */
.layout-app {
  display: flex;
  min-height: 100vh;
}

.layout-sidebar {
  width: 280px;
  background: var(--gray-900);
  color: white;
  padding: var(--space-4);
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.layout-main {
  flex: 1;
  background: var(--gray-50);
  padding: var(--space-6);
  overflow-x: hidden;
}

/* Page Header */
.page-header {
  margin-bottom: var(--space-6);
}

.page-title {
  font-size: var(--text-h1);
  margin-bottom: var(--space-2);
}

.page-subtitle {
  font-size: var(--text-body-lg);
  color: var(--color-text-secondary);
}

/* ============================================
   GRID SYSTEMS
   ============================================ */

/* Card Grid (Auto-fit) */
.grid {
  display: grid;
  gap: var(--space-3);
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

/* Stats Grid (4 columns) */
.stats-grid {
  display: grid;
  gap: var(--space-3);
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

/* Two Column Layout */
.grid-two-column {
  display: grid;
  gap: var(--space-6);
  grid-template-columns: 2fr 1fr;
}

/* ============================================
   RESPONSIVE BREAKPOINTS
   ============================================ */

/* Tablet (768px and down) */
@media (max-width: 768px) {
  .layout-app {
    flex-direction: column;
  }

  .layout-sidebar {
    width: 100%;
    height: auto;
    position: static;
  }

  .layout-main {
    padding: var(--space-4);
  }

  .grid-two-column {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  }
}

/* Mobile (375px and down) */
@media (max-width: 375px) {
  .container {
    padding: 0 var(--space-2);
  }

  .layout-main {
    padding: var(--space-3);
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
```

---

### Phase 2: Template Integration

#### File: `/templates/base.html` (REFACTOR)

**Current Issues:**
- Inline styles scattered throughout
- No design system CSS loading
- Font loading inconsistent
- No CSS variable support

**Changes Needed:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}FCRA Platform{% endblock %}</title>

    <!-- DESIGN SYSTEM CSS (LOAD FIRST) -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/design-system.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/components.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/layouts.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/utilities.css') }}">

    <!-- GOOGLE FONTS -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">

    <!-- PAGE-SPECIFIC CSS -->
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- APP LAYOUT -->
    <div class="layout-app">
        <!-- SIDEBAR NAVIGATION -->
        {% block sidebar %}
        <aside class="layout-sidebar">
            <!-- Navigation content -->
        </aside>
        {% endblock %}

        <!-- MAIN CONTENT -->
        <main class="layout-main">
            {% block content %}{% endblock %}
        </main>
    </div>

    <!-- JAVASCRIPT -->
    <script src="{{ url_for('static', filename='js/interactions.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

**Migration Steps:**
1. Remove all inline `<style>` blocks from base.html
2. Remove hardcoded colors/fonts
3. Add design system CSS links
4. Add Google Fonts link
5. Wrap content in `.layout-app` structure
6. Test that all pages load without style breakage

---

## Component Library Specifications

### Component: Primary Button

**Usage:** Main CTAs, form submissions, primary actions

**HTML Structure:**
```html
<button class="btn btn-primary btn-md">
  Approve & Generate
</button>
```

**Variants:**
```html
<!-- Sizes -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary btn-md">Medium (Default)</button>
<button class="btn btn-primary btn-lg">Large</button>

<!-- With Icon -->
<button class="btn btn-primary btn-md">
  <svg width="20" height="20"><!-- icon --></svg>
  Generate Documents
</button>

<!-- Loading State -->
<button class="btn btn-primary btn-md" disabled>
  <svg class="spinner" width="20" height="20"><!-- spinner --></svg>
  Generating...
</button>

<!-- Disabled -->
<button class="btn btn-primary btn-md" disabled>
  Disabled
</button>
```

**Accessibility:**
- Use `<button>` element, not `<div>` or `<a>`
- Include `aria-label` for icon-only buttons
- Add `disabled` attribute when inactive
- Add `aria-busy="true"` during loading states

**Before/After Example:**

**BEFORE (Current Code):**
```html
<button style="background: #0d9488; color: white; padding: 10px 20px; border-radius: 5px;">
  Approve
</button>
```

**AFTER (Apple-Style):**
```html
<button class="btn btn-primary btn-md">
  Approve & Generate Documents
</button>
```

---

### Component: Client Card

**Usage:** Display client information in list/grid views

**HTML Structure:**
```html
<div class="card card-client card-interactive">
  <div class="card-header">
    <h3 class="card-title">John Doe</h3>
    <span class="badge badge-success">Active</span>
  </div>

  <div class="card-body">
    <div class="client-meta">
      <div class="meta-item">
        <span class="meta-label">Case ID</span>
        <span class="meta-value">BAG-FCRA-2025-0001</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Stage</span>
        <span class="meta-value">Analysis Complete</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Violations</span>
        <span class="meta-value">12 Found</span>
      </div>
    </div>
  </div>

  <div class="card-footer">
    <span class="text-secondary">Updated 2 hours ago</span>
    <button class="btn btn-tertiary btn-sm">View Details</button>
  </div>
</div>
```

**CSS (Additional Styles):**
```css
.client-meta {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meta-label {
  font-size: var(--text-body-sm);
  color: var(--color-text-secondary);
}

.meta-value {
  font-size: var(--text-body);
  font-weight: var(--weight-medium);
  color: var(--color-text-primary);
}
```

**Before/After Example:**

**BEFORE (Table Row):**
```html
<tr>
  <td>1</td>
  <td>John Doe</td>
  <td>BAG-FCRA-2025-0001</td>
  <td>Analysis Complete</td>
  <td>12</td>
  <td>Active</td>
  <td>2 hours ago</td>
  <td><a href="/view/1">View</a></td>
</tr>
```

**AFTER (Card):**
```html
<div class="card card-client card-interactive" onclick="location.href='/view/1'">
  <!-- Card content as shown above -->
</div>
```

---

### Component: Stat Card (Hero Metrics)

**Usage:** Display key metrics on dashboard

**HTML Structure:**
```html
<div class="card card-stat">
  <div class="stat-value">127</div>
  <div class="stat-label">Active Cases</div>
  <div class="stat-change stat-change-positive">
    <svg class="icon-arrow-up"><!-- icon --></svg>
    +12.5% from last month
  </div>
</div>
```

**CSS (Additional Styles):**
```css
.stat-value {
  font-family: var(--font-serif);
  font-size: var(--text-display);
  font-weight: var(--weight-bold);
  color: var(--color-text-primary);
  line-height: 1;
  margin-bottom: var(--space-1);
}

.stat-label {
  font-size: var(--text-body);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.stat-change {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-body-sm);
  font-weight: var(--weight-medium);
}

.stat-change-positive {
  color: var(--color-success);
}

.stat-change-negative {
  color: var(--color-error);
}
```

**Variants:**
```html
<!-- With Sparkline -->
<div class="card card-stat">
  <div class="stat-value">$127K</div>
  <div class="stat-label">Est. Settlement Value</div>
  <svg class="stat-sparkline" width="100" height="24">
    <!-- Sparkline path -->
  </svg>
</div>

<!-- With Icon -->
<div class="card card-stat">
  <div class="stat-icon">
    <svg width="32" height="32"><!-- icon --></svg>
  </div>
  <div class="stat-value">89%</div>
  <div class="stat-label">Case Success Rate</div>
</div>
```

---

### Component: Form Input (Floating Label)

**Usage:** Text inputs with animated labels

**HTML Structure:**
```html
<div class="form-group form-group-floating">
  <input
    type="text"
    id="client-name"
    class="form-input"
    placeholder=" "
    required
  >
  <label for="client-name" class="form-label">Client Name</label>
</div>
```

**Key Details:**
- Input must have `placeholder=" "` (single space) for CSS selector to work
- Label must come AFTER input in HTML
- CSS uses `:focus` and `:not(:placeholder-shown)` to trigger animation

**Validation States:**
```html
<!-- Error State -->
<div class="form-group form-group-floating has-error">
  <input type="email" class="form-input" placeholder=" ">
  <label class="form-label">Email Address</label>
  <span class="form-error">Please enter a valid email</span>
</div>

<!-- Success State -->
<div class="form-group form-group-floating has-success">
  <input type="email" class="form-input" placeholder=" " value="john@example.com">
  <label class="form-label">Email Address</label>
  <span class="form-success">Looks good!</span>
</div>
```

**Additional CSS for Validation:**
```css
.form-group.has-error .form-input {
  border-color: var(--color-error);
}

.form-group.has-error .form-label {
  color: var(--color-error);
}

.form-error {
  display: block;
  margin-top: var(--space-1);
  font-size: var(--text-body-sm);
  color: var(--color-error);
}

.form-group.has-success .form-input {
  border-color: var(--color-success);
}

.form-success {
  display: block;
  margin-top: var(--space-1);
  font-size: var(--text-body-sm);
  color: var(--color-success);
}
```

---

### Component: Modal (Centered)

**Usage:** Confirmations, forms, detail views

**HTML Structure:**
```html
<!-- Modal Backdrop -->
<div class="modal-backdrop" id="modal-backdrop">
  <!-- Modal Container -->
  <div class="modal" role="dialog" aria-labelledby="modal-title">
    <div class="modal-header">
      <h2 class="modal-title" id="modal-title">Confirm Action</h2>
      <button class="btn-icon btn-tertiary" aria-label="Close">
        <svg width="24" height="24"><!-- X icon --></svg>
      </button>
    </div>

    <div class="modal-body">
      <p>Are you sure you want to approve this analysis and generate documents? This will cost approximately $0.</p>
    </div>

    <div class="modal-footer">
      <button class="btn btn-secondary btn-md">Cancel</button>
      <button class="btn btn-primary btn-md">Approve</button>
    </div>
  </div>
</div>
```

**JavaScript for Show/Hide:**
```javascript
// interactions.js

function showModal(modalId) {
  const modal = document.getElementById(modalId);
  modal.style.display = 'block';
  document.body.style.overflow = 'hidden'; // Prevent background scroll
}

function hideModal(modalId) {
  const modal = document.getElementById(modalId);
  modal.style.display = 'none';
  document.body.style.overflow = ''; // Restore scroll
}

// Close on backdrop click
document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) {
      hideModal(backdrop.id);
    }
  });
});

// Close on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      hideModal(backdrop.id);
    });
  }
});
```

**Accessibility:**
- Add `role="dialog"` to modal
- Add `aria-labelledby` pointing to modal title
- Trap focus inside modal when open
- Close on Escape key
- Return focus to trigger element when closed

---

## Screen-by-Screen Implementation Guide

### Screen 1: Dashboard (Priority 1)

**File:** `/templates/dashboard.html`

**Current Issues:**
- Dense table with 10+ columns
- No visual hierarchy
- No whitespace
- Cramped stats at top

**Target Design:**
- Hero metrics grid (4 large stat cards)
- Pipeline visualization
- Recent activity feed
- Quick actions panel

**Implementation Steps:**

#### Step 1: Replace Stats Section

**BEFORE:**
```html
<div class="stats">
  <div style="display: flex; gap: 20px;">
    <div style="background: #f0f0f0; padding: 15px;">
      <p>Active Cases</p>
      <h2>127</h2>
    </div>
    <!-- More stats... -->
  </div>
</div>
```

**AFTER:**
```html
<div class="stats-grid">
  <div class="card card-stat">
    <div class="stat-value">127</div>
    <div class="stat-label">Active Cases</div>
    <div class="stat-change stat-change-positive">
      <svg class="icon-arrow-up" width="16" height="16">
        <path d="M8 4v12m-4-8l4-4 4 4" stroke="currentColor" stroke-width="2" fill="none"/>
      </svg>
      +12.5% from last month
    </div>
  </div>

  <div class="card card-stat">
    <div class="stat-value">$1.2M</div>
    <div class="stat-label">Est. Settlement Value</div>
    <svg class="stat-sparkline" width="100" height="24">
      <!-- Sparkline SVG path -->
    </svg>
  </div>

  <div class="card card-stat">
    <div class="stat-value">34</div>
    <div class="stat-label">Pending Approvals</div>
    <div class="stat-change stat-change-negative">
      <svg class="icon-arrow-down" width="16" height="16">
        <path d="M8 4v12m-4-4l4 4 4-4" stroke="currentColor" stroke-width="2" fill="none"/>
      </svg>
      -5.2% from last week
    </div>
  </div>

  <div class="card card-stat">
    <div class="stat-value">89%</div>
    <div class="stat-label">Success Rate</div>
    <div class="stat-change stat-change-positive">
      <svg class="icon-arrow-up" width="16" height="16">
        <path d="M8 4v12m-4-8l4-4 4 4" stroke="currentColor" stroke-width="2" fill="none"/>
      </svg>
      +2.1% this quarter
    </div>
  </div>
</div>
```

**CSS (Additional):**
```css
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.icon-arrow-up,
.icon-arrow-down {
  width: 16px;
  height: 16px;
}
```

#### Step 2: Add Pipeline Visualization

**NEW SECTION:**
```html
<section class="dashboard-section">
  <h2 class="section-title">Case Pipeline</h2>

  <div class="pipeline-grid">
    <div class="card pipeline-stage">
      <div class="pipeline-header">
        <h3 class="pipeline-title">New Clients</h3>
        <span class="pipeline-count">23</span>
      </div>
      <div class="pipeline-progress">
        <div class="progress-bar" style="width: 45%;"></div>
      </div>
      <p class="pipeline-meta">3 need triage</p>
    </div>

    <div class="card pipeline-stage">
      <div class="pipeline-header">
        <h3 class="pipeline-title">In Analysis</h3>
        <span class="pipeline-count">45</span>
      </div>
      <div class="pipeline-progress">
        <div class="progress-bar" style="width: 78%;"></div>
      </div>
      <p class="pipeline-meta">8 near completion</p>
    </div>

    <div class="card pipeline-stage">
      <div class="pipeline-header">
        <h3 class="pipeline-title">Pending Approval</h3>
        <span class="pipeline-count">34</span>
      </div>
      <div class="pipeline-progress">
        <div class="progress-bar" style="width: 62%;"></div>
      </div>
      <p class="pipeline-meta">12 urgent</p>
    </div>

    <div class="card pipeline-stage">
      <div class="pipeline-header">
        <h3 class="pipeline-title">In Dispute</h3>
        <span class="pipeline-count">25</span>
      </div>
      <div class="pipeline-progress">
        <div class="progress-bar" style="width: 30%;"></div>
      </div>
      <p class="pipeline-meta">5 awaiting response</p>
    </div>
  </div>
</section>
```

**CSS:**
```css
.dashboard-section {
  margin-bottom: var(--space-8);
}

.section-title {
  font-size: var(--text-h2);
  margin-bottom: var(--space-4);
}

.pipeline-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-3);
}

.pipeline-stage {
  padding: var(--space-4);
}

.pipeline-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--space-2);
}

.pipeline-title {
  font-size: var(--text-h4);
  font-weight: var(--weight-semibold);
  color: var(--color-text-primary);
}

.pipeline-count {
  font-family: var(--font-serif);
  font-size: var(--text-h2);
  font-weight: var(--weight-bold);
  color: var(--primary-600);
}

.pipeline-progress {
  height: 8px;
  background: var(--gray-200);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--space-2);
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-500), var(--primary-600));
  border-radius: var(--radius-full);
  transition: width var(--transition-slow);
}

.pipeline-meta {
  font-size: var(--text-body-sm);
  color: var(--color-text-secondary);
  margin: 0;
}
```

#### Step 3: Replace Cases Table with Activity Feed

**BEFORE:**
```html
<table class="cases-table">
  <tr>
    <th>ID</th>
    <th>Client</th>
    <th>Case #</th>
    <th>Stage</th>
    <th>Violations</th>
    <th>Status</th>
    <th>Updated</th>
    <th>Actions</th>
  </tr>
  <!-- 50+ rows -->
</table>
```

**AFTER:**
```html
<section class="dashboard-section">
  <div class="section-header">
    <h2 class="section-title">Recent Activity</h2>
    <a href="/cases" class="btn btn-tertiary btn-sm">View All Cases</a>
  </div>

  <div class="activity-feed">
    <div class="activity-item">
      <div class="activity-icon activity-icon-success">
        <svg width="20" height="20"><!-- checkmark icon --></svg>
      </div>
      <div class="activity-content">
        <p class="activity-title">
          <strong>John Doe</strong> case analysis completed
        </p>
        <p class="activity-meta">
          12 violations found • Ready for approval
        </p>
      </div>
      <div class="activity-actions">
        <button class="btn btn-primary btn-sm">Review</button>
      </div>
      <div class="activity-time">2 hours ago</div>
    </div>

    <div class="activity-item">
      <div class="activity-icon activity-icon-info">
        <svg width="20" height="20"><!-- document icon --></svg>
      </div>
      <div class="activity-content">
        <p class="activity-title">
          <strong>Jane Smith</strong> documents generated
        </p>
        <p class="activity-meta">
          Internal analysis, client report, email sent
        </p>
      </div>
      <div class="activity-actions">
        <button class="btn btn-tertiary btn-sm">View</button>
      </div>
      <div class="activity-time">5 hours ago</div>
    </div>

    <!-- More activity items... -->
  </div>
</section>
```

**CSS:**
```css
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.activity-feed {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.activity-item {
  display: grid;
  grid-template-columns: 40px 1fr auto auto;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-3);
  background: white;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  transition: all var(--transition-base);
}

.activity-item:hover {
  box-shadow: var(--shadow-md);
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
}

.activity-icon-success {
  background: var(--color-success);
  color: white;
}

.activity-icon-info {
  background: var(--primary-100);
  color: var(--primary-700);
}

.activity-content {
  min-width: 0; /* Allow text truncation */
}

.activity-title {
  font-size: var(--text-body);
  color: var(--color-text-primary);
  margin: 0 0 4px 0;
}

.activity-meta {
  font-size: var(--text-body-sm);
  color: var(--color-text-secondary);
  margin: 0;
}

.activity-time {
  font-size: var(--text-body-sm);
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .activity-item {
    grid-template-columns: 40px 1fr;
    gap: var(--space-2);
  }

  .activity-actions,
  .activity-time {
    grid-column: 2;
    justify-self: start;
  }
}
```

**Full Dashboard Structure:**
```html
{% extends "base.html" %}

{% block content %}
<div class="container">
  <!-- Page Header -->
  <div class="page-header">
    <h1 class="page-title">Dashboard</h1>
    <p class="page-subtitle">Overview of your FCRA case management</p>
  </div>

  <!-- Hero Stats -->
  <div class="stats-grid">
    <!-- 4 stat cards as shown above -->
  </div>

  <!-- Pipeline Visualization -->
  <section class="dashboard-section">
    <h2 class="section-title">Case Pipeline</h2>
    <div class="pipeline-grid">
      <!-- 4 pipeline stage cards -->
    </div>
  </section>

  <!-- Recent Activity Feed -->
  <section class="dashboard-section">
    <div class="section-header">
      <h2 class="section-title">Recent Activity</h2>
      <a href="/cases" class="btn btn-tertiary btn-sm">View All Cases</a>
    </div>
    <div class="activity-feed">
      <!-- Activity items -->
    </div>
  </section>

  <!-- Quick Actions (Optional) -->
  <section class="dashboard-section">
    <h2 class="section-title">Quick Actions</h2>
    <div class="quick-actions">
      <button class="btn btn-primary btn-lg">
        <svg width="24" height="24"><!-- icon --></svg>
        New Case
      </button>
      <button class="btn btn-secondary btn-lg">
        <svg width="24" height="24"><!-- icon --></svg>
        Bulk Upload
      </button>
      <button class="btn btn-secondary btn-lg">
        <svg width="24" height="24"><!-- icon --></svg>
        Generate Report
      </button>
    </div>
  </section>
</div>
{% endblock %}
```

---

### Screen 2: Client List (Priority 2)

**File:** `/templates/client_list.html` or equivalent

**Current Issues:**
- Dense 10-column table
- No filtering/search UI
- No bulk actions toolbar
- No card/grid view option

**Target Design:**
- Card grid layout (3-4 columns)
- Prominent search bar
- Filter chips (Status, Stage, Date)
- Bulk actions toolbar (appears when items selected)
- Toggle between card/list views

**Implementation Steps:**

#### Step 1: Add Search & Filter Bar

**NEW SECTION:**
```html
<div class="filter-bar">
  <div class="search-box">
    <svg class="search-icon" width="20" height="20">
      <path d="M9 17A8 8 0 1 0 9 1a8 8 0 0 0 0 16zm6-2l4 4" stroke="currentColor" stroke-width="2" fill="none"/>
    </svg>
    <input
      type="text"
      class="search-input"
      placeholder="Search clients, case IDs, emails..."
      id="client-search"
    >
  </div>

  <div class="filter-chips">
    <button class="chip chip-active" data-filter="all">
      All Cases
      <span class="chip-count">127</span>
    </button>
    <button class="chip" data-filter="active">
      Active
      <span class="chip-count">89</span>
    </button>
    <button class="chip" data-filter="pending">
      Pending Approval
      <span class="chip-count">34</span>
    </button>
    <button class="chip" data-filter="completed">
      Completed
      <span class="chip-count">4</span>
    </button>
  </div>

  <div class="filter-actions">
    <button class="btn btn-tertiary btn-icon" aria-label="Advanced filters">
      <svg width="20" height="20"><!-- filter icon --></svg>
    </button>
    <button class="btn btn-tertiary btn-icon" aria-label="Toggle view">
      <svg width="20" height="20"><!-- grid icon --></svg>
    </button>
    <button class="btn btn-primary btn-md">
      <svg width="20" height="20"><!-- plus icon --></svg>
      New Case
    </button>
  </div>
</div>
```

**CSS:**
```css
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
  margin-bottom: var(--space-6);
  padding: var(--space-3);
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 300px;
}

.search-icon {
  position: absolute;
  left: var(--space-2);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 44px;
  padding: 12px 12px 12px 44px;
  font-size: var(--text-body);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.filter-chips {
  display: flex;
  gap: var(--space-1);
  flex-wrap: wrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 8px var(--space-2);
  font-size: var(--text-body-sm);
  font-weight: var(--weight-medium);
  background: var(--gray-100);
  color: var(--gray-700);
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.chip:hover {
  background: var(--gray-200);
}

.chip-active,
.chip.active {
  background: var(--primary-100);
  color: var(--primary-700);
  border-color: var(--primary-300);
}

.chip-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  font-size: 11px;
  font-weight: var(--weight-semibold);
  background: white;
  border-radius: var(--radius-full);
}

.filter-actions {
  display: flex;
  gap: var(--space-2);
  margin-left: auto;
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    min-width: 100%;
  }

  .filter-actions {
    margin-left: 0;
    justify-content: space-between;
  }
}
```

#### Step 2: Replace Table with Card Grid

**BEFORE:**
```html
<table class="client-table">
  <thead>
    <tr>
      <th><input type="checkbox"></th>
      <th>ID</th>
      <th>Client Name</th>
      <th>Case #</th>
      <th>Email</th>
      <th>Stage</th>
      <th>Violations</th>
      <th>Status</th>
      <th>Updated</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><input type="checkbox"></td>
      <td>1</td>
      <td>John Doe</td>
      <td>BAG-FCRA-2025-0001</td>
      <td>john@example.com</td>
      <td>Analysis Complete</td>
      <td>12</td>
      <td><span class="badge-success">Active</span></td>
      <td>2 hours ago</td>
      <td><a href="/view/1">View</a></td>
    </tr>
    <!-- More rows... -->
  </tbody>
</table>
```

**AFTER:**
```html
<div class="client-grid">
  <div class="card card-client card-interactive" data-client-id="1">
    <div class="card-checkbox">
      <input type="checkbox" id="client-1" class="client-checkbox">
    </div>

    <div class="card-header">
      <h3 class="card-title">John Doe</h3>
      <span class="badge badge-success">Active</span>
    </div>

    <div class="card-body">
      <div class="client-meta">
        <div class="meta-item">
          <span class="meta-label">Case ID</span>
          <span class="meta-value">BAG-FCRA-2025-0001</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Email</span>
          <span class="meta-value">john@example.com</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Stage</span>
          <span class="meta-value">Analysis Complete</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Violations</span>
          <span class="meta-value meta-value-highlight">12 Found</span>
        </div>
      </div>
    </div>

    <div class="card-footer">
      <span class="text-secondary">Updated 2 hours ago</span>
      <button class="btn btn-tertiary btn-sm" onclick="viewClient(1)">
        View Details
      </button>
    </div>
  </div>

  <!-- More client cards... -->
</div>
```

**CSS:**
```css
.client-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-3);
}

.card-client {
  position: relative;
  cursor: pointer;
  transition: all var(--transition-base);
}

.card-client:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.card-checkbox {
  position: absolute;
  top: var(--space-2);
  left: var(--space-2);
  z-index: 10;
}

.client-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.card-client .card-header {
  padding-left: var(--space-5); /* Make room for checkbox */
}

.meta-value-highlight {
  color: var(--primary-600);
  font-weight: var(--weight-semibold);
}

@media (max-width: 768px) {
  .client-grid {
    grid-template-columns: 1fr;
  }
}
```

#### Step 3: Add Bulk Actions Toolbar

**NEW SECTION (Appears when checkboxes selected):**
```html
<div class="bulk-toolbar" id="bulk-toolbar" style="display: none;">
  <div class="bulk-toolbar-content">
    <div class="bulk-info">
      <span class="bulk-count" id="bulk-count">0</span> selected
    </div>

    <div class="bulk-actions">
      <button class="btn btn-secondary btn-sm">
        <svg width="16" height="16"><!-- export icon --></svg>
        Export
      </button>
      <button class="btn btn-secondary btn-sm">
        <svg width="16" height="16"><!-- email icon --></svg>
        Email
      </button>
      <button class="btn btn-secondary btn-sm">
        <svg width="16" height="16"><!-- archive icon --></svg>
        Archive
      </button>
      <button class="btn btn-primary btn-sm">
        <svg width="16" height="16"><!-- checkmark icon --></svg>
        Approve All
      </button>
    </div>

    <button class="btn-icon btn-tertiary" onclick="clearSelection()">
      <svg width="20" height="20"><!-- X icon --></svg>
    </button>
  </div>
</div>
```

**CSS:**
```css
.bulk-toolbar {
  position: fixed;
  bottom: var(--space-4);
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--z-sticky);
  animation: slideUp var(--transition-base);
}

.bulk-toolbar-content {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4);
  background: var(--gray-900);
  color: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-2xl);
}

.bulk-info {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.bulk-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0 8px;
  font-weight: var(--weight-bold);
  background: var(--primary-600);
  border-radius: var(--radius-full);
}

.bulk-actions {
  display: flex;
  gap: var(--space-1);
}
```

**JavaScript:**
```javascript
// interactions.js

let selectedClients = new Set();

// Listen for checkbox changes
document.addEventListener('DOMContentLoaded', () => {
  const checkboxes = document.querySelectorAll('.client-checkbox');
  const bulkToolbar = document.getElementById('bulk-toolbar');
  const bulkCount = document.getElementById('bulk-count');

  checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
      const clientId = e.target.closest('[data-client-id]').dataset.clientId;

      if (e.target.checked) {
        selectedClients.add(clientId);
      } else {
        selectedClients.delete(clientId);
      }

      // Update toolbar
      if (selectedClients.size > 0) {
        bulkToolbar.style.display = 'block';
        bulkCount.textContent = selectedClients.size;
      } else {
        bulkToolbar.style.display = 'none';
      }
    });
  });
});

function clearSelection() {
  selectedClients.clear();
  document.querySelectorAll('.client-checkbox').forEach(cb => cb.checked = false);
  document.getElementById('bulk-toolbar').style.display = 'none';
}

function viewClient(clientId) {
  window.location.href = `/client/${clientId}`;
}
```

**Full Client List Structure:**
```html
{% extends "base.html" %}

{% block content %}
<div class="container">
  <!-- Page Header -->
  <div class="page-header">
    <h1 class="page-title">Client List</h1>
    <p class="page-subtitle">Manage all FCRA cases</p>
  </div>

  <!-- Search & Filter Bar -->
  <div class="filter-bar">
    <!-- Search box, filter chips, actions -->
  </div>

  <!-- Client Grid -->
  <div class="client-grid" id="client-grid">
    <!-- Client cards (dynamically generated) -->
  </div>

  <!-- Bulk Actions Toolbar (Fixed Position) -->
  <div class="bulk-toolbar" id="bulk-toolbar" style="display: none;">
    <!-- Bulk actions -->
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
  // Client list interactions
</script>
{% endblock %}
```

---

### Screen 3: Client Portal (Priority 3)

**File:** `/templates/client_portal.html`

**Current Issues:**
- 7 tabs (overwhelming)
- Dense information
- No personalization
- Desktop-only layout

**Target Design:**
- Hero section with client name + progress ring
- 4 simplified tabs (Overview, Documents, Timeline, Contact)
- Card-based content layout
- Mobile-responsive (stacked layout)

**Implementation Steps:**

#### Step 1: Add Hero Section

**NEW SECTION:**
```html
<div class="portal-hero">
  <div class="hero-content">
    <div class="hero-greeting">
      <p class="hero-label">Welcome back,</p>
      <h1 class="hero-title">John Doe</h1>
      <p class="hero-subtitle">Case #BAG-FCRA-2025-0001</p>
    </div>

    <div class="hero-stats">
      <!-- Progress Ring -->
      <div class="progress-ring">
        <svg width="120" height="120">
          <circle cx="60" cy="60" r="54" fill="none" stroke="var(--gray-200)" stroke-width="8"/>
          <circle cx="60" cy="60" r="54" fill="none" stroke="var(--primary-600)" stroke-width="8"
                  stroke-dasharray="339.29" stroke-dashoffset="84.82"
                  transform="rotate(-90 60 60)" stroke-linecap="round"/>
        </svg>
        <div class="progress-center">
          <div class="progress-value">75%</div>
          <div class="progress-label">Complete</div>
        </div>
      </div>

      <div class="hero-metrics">
        <div class="hero-metric">
          <div class="metric-value">12</div>
          <div class="metric-label">Violations Found</div>
        </div>
        <div class="hero-metric">
          <div class="metric-value">$5.2K</div>
          <div class="metric-label">Est. Settlement</div>
        </div>
      </div>
    </div>
  </div>
</div>
```

**CSS:**
```css
.portal-hero {
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%);
  color: white;
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  margin-bottom: var(--space-6);
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-6);
}

.hero-label {
  font-size: var(--text-body);
  opacity: 0.9;
  margin-bottom: var(--space-1);
}

.hero-title {
  font-size: var(--text-display);
  font-weight: var(--weight-bold);
  margin-bottom: var(--space-1);
}

.hero-subtitle {
  font-size: var(--text-body-lg);
  opacity: 0.8;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.progress-ring {
  position: relative;
  width: 120px;
  height: 120px;
}

.progress-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.progress-value {
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: var(--weight-bold);
  line-height: 1;
}

.progress-label {
  font-size: var(--text-caption);
  opacity: 0.8;
  margin-top: 4px;
}

.hero-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.hero-metric {
  text-align: right;
}

.hero-metric .metric-value {
  font-family: var(--font-serif);
  font-size: var(--text-h2);
  font-weight: var(--weight-bold);
  line-height: 1;
}

.hero-metric .metric-label {
  font-size: var(--text-body-sm);
  opacity: 0.8;
}

@media (max-width: 768px) {
  .portal-hero {
    padding: var(--space-4);
  }

  .hero-content {
    flex-direction: column;
    text-align: center;
  }

  .hero-metrics {
    flex-direction: row;
  }

  .hero-metric {
    text-align: center;
  }
}
```

#### Step 2: Simplify Tabs (7 → 4)

**BEFORE:**
```html
<div class="tabs">
  <button>Overview</button>
  <button>Documents</button>
  <button>Violations</button>
  <button>Timeline</button>
  <button>Damages</button>
  <button>Letters</button>
  <button>Contact</button>
</div>
```

**AFTER:**
```html
<div class="tab-bar">
  <button class="tab tab-active" data-tab="overview">
    <svg class="tab-icon" width="20" height="20"><!-- home icon --></svg>
    <span class="tab-label">Overview</span>
  </button>
  <button class="tab" data-tab="documents">
    <svg class="tab-icon" width="20" height="20"><!-- document icon --></svg>
    <span class="tab-label">Documents</span>
  </button>
  <button class="tab" data-tab="timeline">
    <svg class="tab-icon" width="20" height="20"><!-- clock icon --></svg>
    <span class="tab-label">Timeline</span>
  </button>
  <button class="tab" data-tab="contact">
    <svg class="tab-icon" width="20" height="20"><!-- message icon --></svg>
    <span class="tab-label">Contact</span>
  </button>
</div>

<div class="tab-content">
  <div id="tab-overview" class="tab-pane tab-pane-active">
    <!-- Overview content (combines violations + damages) -->
  </div>
  <div id="tab-documents" class="tab-pane">
    <!-- Documents content (combines documents + letters) -->
  </div>
  <div id="tab-timeline" class="tab-pane">
    <!-- Timeline content -->
  </div>
  <div id="tab-contact" class="tab-pane">
    <!-- Contact content -->
  </div>
</div>
```

**CSS:**
```css
.tab-bar {
  display: flex;
  gap: var(--space-1);
  padding: var(--space-1);
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  margin-bottom: var(--space-6);
}

.tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab:hover {
  background: var(--gray-50);
}

.tab-active {
  background: var(--primary-100);
  color: var(--primary-700);
}

.tab-icon {
  width: 20px;
  height: 20px;
}

.tab-label {
  font-size: var(--text-body-sm);
  font-weight: var(--weight-medium);
}

.tab-content {
  min-height: 400px;
}

.tab-pane {
  display: none;
  animation: fadeIn var(--transition-base);
}

.tab-pane-active {
  display: block;
}

@media (max-width: 768px) {
  .tab {
    padding: var(--space-2) var(--space-1);
  }

  .tab-label {
    font-size: var(--text-caption);
  }
}
```

**JavaScript:**
```javascript
// interactions.js

function initTabs() {
  const tabs = document.querySelectorAll('.tab');
  const panes = document.querySelectorAll('.tab-pane');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = `tab-${tab.dataset.tab}`;

      // Deactivate all tabs and panes
      tabs.forEach(t => t.classList.remove('tab-active'));
      panes.forEach(p => p.classList.remove('tab-pane-active'));

      // Activate clicked tab and corresponding pane
      tab.classList.add('tab-active');
      document.getElementById(targetId).classList.add('tab-pane-active');
    });
  });
}

document.addEventListener('DOMContentLoaded', initTabs);
```

#### Step 3: Overview Tab Content (Card-Based)

**CONTENT:**
```html
<div id="tab-overview" class="tab-pane tab-pane-active">
  <!-- Status Card -->
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">Case Status</h3>
      <span class="badge badge-success">Analysis Complete</span>
    </div>
    <div class="card-body">
      <div class="status-timeline">
        <div class="status-step status-step-complete">
          <div class="status-icon">
            <svg width="20" height="20"><!-- checkmark --></svg>
          </div>
          <div class="status-content">
            <p class="status-title">Credit Report Submitted</p>
            <p class="status-meta">December 10, 2025</p>
          </div>
        </div>
        <div class="status-step status-step-complete">
          <div class="status-icon">
            <svg width="20" height="20"><!-- checkmark --></svg>
          </div>
          <div class="status-content">
            <p class="status-title">Analysis Completed</p>
            <p class="status-meta">December 12, 2025</p>
          </div>
        </div>
        <div class="status-step status-step-active">
          <div class="status-icon">
            <svg width="20" height="20"><!-- clock --></svg>
          </div>
          <div class="status-content">
            <p class="status-title">Awaiting Your Approval</p>
            <p class="status-meta">Current step</p>
          </div>
        </div>
        <div class="status-step">
          <div class="status-icon">
            <svg width="20" height="20"><!-- circle --></svg>
          </div>
          <div class="status-content">
            <p class="status-title">Dispute Letters Sent</p>
            <p class="status-meta">Pending</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Violations Summary Card -->
  <div class="grid-two-column" style="margin-top: var(--space-4);">
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Violations Found</h3>
      </div>
      <div class="card-body">
        <div class="violation-list">
          <div class="violation-item">
            <div class="violation-type">Inaccurate Information</div>
            <div class="violation-count">8 violations</div>
          </div>
          <div class="violation-item">
            <div class="violation-type">Failure to Investigate</div>
            <div class="violation-count">3 violations</div>
          </div>
          <div class="violation-item">
            <div class="violation-type">Improper Verification</div>
            <div class="violation-count">1 violation</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Damages Card -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Settlement Estimate</h3>
      </div>
      <div class="card-body">
        <div class="damage-breakdown">
          <div class="damage-item">
            <span class="damage-label">Statutory Damages</span>
            <span class="damage-value">$3,500</span>
          </div>
          <div class="damage-item">
            <span class="damage-label">Actual Damages</span>
            <span class="damage-value">$1,200</span>
          </div>
          <div class="damage-item">
            <span class="damage-label">Potential Punitive</span>
            <span class="damage-value">$500</span>
          </div>
          <div class="damage-total">
            <span class="damage-label">Target Settlement</span>
            <span class="damage-value">$5,200</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

**CSS:**
```css
.status-timeline {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.status-step {
  display: flex;
  gap: var(--space-2);
  position: relative;
  padding-left: var(--space-3);
}

.status-step:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 19px;
  top: 40px;
  bottom: -24px;
  width: 2px;
  background: var(--gray-200);
}

.status-step-complete::before {
  background: var(--color-success);
}

.status-step-active::before {
  background: var(--primary-500);
}

.status-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gray-100);
  color: var(--gray-400);
  flex-shrink: 0;
}

.status-step-complete .status-icon {
  background: var(--color-success);
  color: white;
}

.status-step-active .status-icon {
  background: var(--primary-500);
  color: white;
}

.status-title {
  font-weight: var(--weight-medium);
  color: var(--color-text-primary);
  margin: 0;
}

.status-meta {
  font-size: var(--text-body-sm);
  color: var(--color-text-secondary);
  margin: 0;
}

.violation-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.violation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2);
  background: var(--gray-50);
  border-radius: var(--radius-md);
}

.violation-type {
  font-weight: var(--weight-medium);
}

.violation-count {
  color: var(--primary-600);
  font-weight: var(--weight-semibold);
}

.damage-breakdown {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.damage-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--color-border);
}

.damage-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) 0;
  margin-top: var(--space-2);
  padding-top: var(--space-3);
  border-top: 2px solid var(--gray-300);
}

.damage-total .damage-value {
  font-family: var(--font-serif);
  font-size: var(--text-h3);
  font-weight: var(--weight-bold);
  color: var(--primary-600);
}
```

---

## Migration Strategy

### Phase 1: Design System Foundation (Week 1)

**Tasks:**
1. Create `static/css/design-system.css`
2. Create `static/css/components.css`
3. Create `static/css/layouts.css`
4. Create `static/css/utilities.css`
5. Update `templates/base.html` to load new CSS files
6. Add Google Fonts link
7. Test that all pages load without breaking

**Success Criteria:**
- All 4 CSS files created
- Base.html loads new CSS
- No visual regressions on existing pages
- Fonts load correctly

**Rollback Plan:**
- Revert base.html changes
- Keep new CSS files (unused)

---

### Phase 2: Dashboard Redesign (Week 2)

**Tasks:**
1. Backup `templates/dashboard.html` to `dashboard_legacy.html`
2. Replace stats section with hero metrics grid
3. Add pipeline visualization section
4. Replace cases table with activity feed
5. Test responsive breakpoints (1440px, 768px, 375px)
6. Validate all links/buttons work

**Success Criteria:**
- Dashboard loads with new design
- All stats display correctly
- Activity feed shows recent cases
- Mobile layout works
- No broken links

**Rollback Plan:**
- Rename `dashboard_legacy.html` back to `dashboard.html`

---

### Phase 3: Client List Redesign (Week 3)

**Tasks:**
1. Backup `templates/client_list.html`
2. Add search & filter bar
3. Replace table with card grid
4. Implement bulk actions toolbar
5. Add JavaScript for checkboxes and filtering
6. Test with 0, 1, 10, 100 clients

**Success Criteria:**
- Card grid displays clients
- Search filters results
- Filter chips work
- Bulk toolbar appears when selecting
- All actions functional

**Rollback Plan:**
- Restore backup

---

### Phase 4: Client Portal Redesign (Week 4)

**Tasks:**
1. Backup `templates/client_portal.html`
2. Add hero section with progress ring
3. Simplify tabs (7 → 4)
4. Redesign Overview tab content
5. Redesign Documents tab
6. Test mobile responsive layout

**Success Criteria:**
- Hero displays client info + progress
- 4 tabs load correctly
- Tab switching works
- Mobile layout stacks properly

**Rollback Plan:**
- Restore backup

---

### Phase 5: Remaining Screens (Weeks 5-6)

**Priority Order:**
1. Analysis Review (moderate refactor)
2. Dispute Letters (moderate refactor)
3. Triage Queue (moderate refactor)
4. Settings pages (minor updates)
5. Auth pages (minor updates)

**Strategy:**
- One screen per day
- Follow same backup → refactor → test pattern
- Apply design system components consistently

---

### Phase 6: Polish & Optimization (Week 7-8)

**Tasks:**
1. Add animations and transitions
2. Optimize images and fonts
3. Accessibility audit (WCAG 2.1 AA)
4. Performance audit (Lighthouse)
5. Cross-browser testing (Chrome, Safari, Firefox)
6. User acceptance testing

**Success Criteria:**
- Lighthouse score > 90 (Performance, Accessibility, Best Practices)
- All animations smooth (60fps)
- No WCAG violations
- Works in all major browsers

---

## Testing & Validation

### Testing Checklist

#### Visual Regression Testing
- [ ] Compare screenshots before/after for each screen
- [ ] Verify colors match design system (use browser dev tools color picker)
- [ ] Check typography (font family, size, weight, line height)
- [ ] Validate spacing uses 8px grid (inspect with ruler tool)
- [ ] Confirm shadows match elevation system

#### Responsive Testing
- [ ] Test at 1440px (desktop)
- [ ] Test at 1024px (small desktop)
- [ ] Test at 768px (tablet)
- [ ] Test at 375px (mobile)
- [ ] Test at 320px (small mobile)
- [ ] Verify no horizontal scroll at any breakpoint
- [ ] Check touch targets ≥ 44px on mobile

#### Functional Testing
- [ ] All buttons trigger correct actions
- [ ] Forms submit successfully
- [ ] Modals open/close correctly
- [ ] Tabs switch properly
- [ ] Search filters results
- [ ] Bulk selection works
- [ ] Links navigate correctly

#### Accessibility Testing
- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Focus indicators visible
- [ ] Color contrast ≥ 4.5:1 for text
- [ ] Screen reader announces content correctly
- [ ] Form labels associated with inputs
- [ ] Buttons have aria-labels (icon-only)
- [ ] Modals trap focus

#### Performance Testing
- [ ] Page load < 2 seconds
- [ ] Time to interactive < 3 seconds
- [ ] Animations run at 60fps
- [ ] No layout shifts (CLS < 0.1)
- [ ] Images optimized (WebP, lazy load)
- [ ] CSS minified for production

#### Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Safari (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

### Validation Tools

**Automated Testing:**
```bash
# Lighthouse CI
npm install -g @lhci/cli
lhci autorun --collect.url=http://localhost:5000 --assert.preset=lighthouse:recommended

# Accessibility (axe)
npm install -g @axe-core/cli
axe http://localhost:5000 --tags wcag2a,wcag2aa

# Visual regression (BackstopJS)
npm install -g backstopjs
backstop test
```

**Manual Testing:**
```bash
# Test different screen sizes
# Chrome DevTools > Device Toolbar > Responsive

# Test keyboard navigation
# Tab through all interactive elements
# Enter/Space to activate buttons
# Escape to close modals

# Test with screen reader
# macOS: VoiceOver (Cmd+F5)
# Windows: NVDA (free)
```

---

## Developer Handoff Checklist

### Before Development Starts

- [ ] Design system CSS files created and reviewed
- [ ] Component library documented with examples
- [ ] All screen mockups reviewed and approved
- [ ] Typography/color tokens finalized
- [ ] Icon library selected (e.g., Heroicons, SF Symbols)
- [ ] Responsive breakpoints agreed upon
- [ ] Animation timing/easing curves defined

### During Development

- [ ] Developer has access to Figma file (if using Figma)
- [ ] Developer understands design system structure
- [ ] Code review process established
- [ ] Weekly design QA sessions scheduled
- [ ] Feedback loop for design adjustments
- [ ] Testing strategy documented

### After Implementation

- [ ] Design system documented in Storybook or similar
- [ ] Component usage guidelines written
- [ ] Accessibility testing completed
- [ ] Performance benchmarks met
- [ ] Cross-browser testing passed
- [ ] User acceptance testing completed
- [ ] Design tokens exported to JSON (for future tools)

---

## Appendix: Quick Reference

### Color Palette
```css
/* Primary (Teal) */
--primary-600: #0d9488;  /* Main brand */
--primary-700: #0f766e;  /* Hover */
--primary-100: #ccfbf1;  /* Light background */

/* Grays */
--gray-50: #f9fafb;     /* Page background */
--gray-200: #e5e7eb;    /* Borders */
--gray-600: #4b5563;    /* Secondary text */
--gray-900: #111827;    /* Primary text */

/* Semantic */
--color-success: #10b981;
--color-error: #ef4444;
--color-warning: #f59e0b;
```

### Typography Scale
```css
--text-display: 56px;   /* Hero headlines */
--text-h1: 48px;        /* Page titles */
--text-h2: 36px;        /* Section headers */
--text-body: 16px;      /* Body copy */
--text-caption: 12px;   /* Labels */
```

### Spacing Scale (8px grid)
```css
--space-1: 8px;
--space-2: 16px;
--space-3: 24px;
--space-4: 32px;
--space-6: 48px;
--space-8: 64px;
```

### Common Patterns

**Button:**
```html
<button class="btn btn-primary btn-md">Label</button>
```

**Card:**
```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Title</h3>
  </div>
  <div class="card-body">Content</div>
</div>
```

**Form Input:**
```html
<div class="form-group">
  <label class="form-label" for="input-id">Label</label>
  <input type="text" id="input-id" class="form-input" placeholder="Placeholder">
</div>
```

**Badge:**
```html
<span class="badge badge-success">Active</span>
```

---

## Document End

**Next Steps:**
1. Review this blueprint with development team
2. Clarify any questions about implementation
3. Create development tickets from this blueprint
4. Start with Phase 1 (Design System Foundation)
5. Schedule weekly design QA reviews

**Questions?** Refer to:
- APPLE_DESIGN_GAP_ANALYSIS.md (design rationale)
- FIGMA_DESIGN_SPECIFICATION.md (visual reference)
- This document (implementation details)

**Document Status:** ✅ Ready for Development
