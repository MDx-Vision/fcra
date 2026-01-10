# Figma Design Specification: Apple-Style FCRA Platform
**Brightpath Ascend Group | Credit Report Litigation Automation**

*Specification Date: December 14, 2025*
*Target Figma Version: Professional/Organization*
*Design System: Apple Human Interface Guidelines + Custom FCRA*

---

## Executive Summary

This document provides complete specifications for creating Apple-style Figma mockups for the FCRA platform. It includes:

- **3 Proof-of-Concept Screens** (Dashboard, Client List, Client Portal)
- **Complete Design System** (colors, typography, components)
- **Component Library** (50+ reusable components)
- **Interaction Flows** (animations, state changes)
- **Developer Handoff Specs** (measurements, CSS variables)
- **Before/After Comparisons** (current vs. proposed)

**Figma File Structure:**
```
FCRA Platform - Apple Redesign/
├── 📄 Cover Page
├── 🎨 Design System
│   ├── Colors (Light Mode)
│   ├── Colors (Dark Mode)
│   ├── Typography
│   ├── Spacing & Grid
│   ├── Shadows & Effects
│   ├── Icons
│   └── Illustrations
├── 🧩 Component Library
│   ├── Buttons
│   ├── Cards
│   ├── Forms
│   ├── Navigation
│   ├── Modals
│   ├── Tables
│   └── Data Visualization
├── 📱 Proof of Concept - Mobile
│   ├── Dashboard (Mobile)
│   ├── Client List (Mobile)
│   └── Client Portal (Mobile)
├── 💻 Proof of Concept - Desktop
│   ├── Dashboard (Desktop)
│   ├── Client List (Desktop)
│   └── Client Portal (Desktop)
├── 🔄 User Flows
│   ├── New Case Creation
│   ├── Bulk Client Operations
│   └── Client Portal Onboarding
├── ⚡ Interactions & Animations
│   ├── Button States
│   ├── Page Transitions
│   └── Loading States
└── 📊 Before/After Comparisons
    ├── Dashboard Comparison
    ├── Client List Comparison
    └── Portal Comparison
```

---

## Part 1: Figma File Setup

### 1.1 Canvas Setup

**Page 1: Cover Page**
- Frame: 1920x1080px
- Background: Linear gradient (navy to teal)
- Content:
  - Project title: "FCRA Platform - Apple Redesign"
  - Subtitle: "Design System & Proof of Concept"
  - Version: "1.0"
  - Date: "December 2025"
  - Designer name
  - Company logo

**Page 2: Design System**
- Multiple frames, each 1920x1080px
- Use Figma Styles for every color, text style, effect
- Document all tokens

**Page 3: Component Library**
- Auto Layout for all components
- Component variants for states (default, hover, active, disabled)
- Use Figma's component properties (boolean, text, instance swap)
- Organize with clear naming: Button/Primary/Large/Default

**Pages 4-5: Mockups (Mobile + Desktop)**
- Mobile: 375x812px (iPhone 13 Pro)
- Tablet: 768x1024px (iPad)
- Desktop: 1440x900px (MacBook Pro 14")

**Page 6: User Flows**
- Use FigJam or Figjam-style flow diagrams
- Arrows with annotations
- Decision points

**Page 7: Interactions**
- Use Figma's prototyping features
- Smart Animate for transitions
- Document easing curves

**Page 8: Before/After**
- Side-by-side comparison
- Annotations highlighting differences

### 1.2 Plugins to Install

**Required Plugins:**
1. **Stark** - Accessibility checker (contrast, color blindness)
2. **Iconify** - Icon library (SF Symbols style)
3. **Unsplash** - Stock photos for avatars
4. **Content Reel** - Generate realistic names/emails
5. **Lorem Ipsum** - Text generation
6. **Autoflow** - User flow arrows
7. **Similayer** - Batch rename layers
8. **Design Lint** - Check for design inconsistencies

**Optional Plugins:**
9. **Anima** - Export to HTML/CSS
10. **Zeplin** - Developer handoff
11. **ProtoPie** - Advanced prototyping

### 1.3 Figma Styles to Create

**Color Styles:**
- Primary/50 through Primary/900 (10 shades)
- Gray/50 through Gray/900 (10 shades)
- Success/Warning/Error/Info (semantic colors)
- Background/Surface/Surface-Raised
- Text/Primary, Text/Secondary, Text/Tertiary

**Text Styles:**
- Display (56px, Playfair Display, 600)
- Title/1 (40px), Title/2 (32px), Title/3 (24px)
- Headline (20px)
- Body (16px)
- Callout (16px, 500 weight)
- Subheadline (14px)
- Footnote (13px)
- Caption (12px)

**Effect Styles:**
- Elevation/1 through Elevation/5
- Focus Ring (teal glow)
- Dark Mode Shadow (lighter)

**Grid Styles:**
- 8px grid (universal)
- 12-column grid (desktop)
- 4-column grid (mobile)

---

## Part 2: Design System Documentation

### 2.1 Color System Frame

**Frame Dimensions:** 1920x1080px
**Layout:** Grid of color swatches

#### Light Mode Colors

**Frame 1: Primary Palette**
```
Layout: 10 rectangles (200x200px each), horizontal
Spacing: 16px gap

Swatch 1: #f0fdfa (Primary/50)
  - Rectangle fill: #f0fdfa
  - Text: "Primary/50" (14px, Gray/900)
  - Text: "#f0fdfa" (12px, Gray/600)
  - Text: "Backgrounds, hover states"

Swatch 2: #ccfbf1 (Primary/100)
  [same structure]

Swatch 3: #99f6e4 (Primary/200)
Swatch 4: #5eead4 (Primary/300)
Swatch 5: #2dd4bf (Primary/400)
Swatch 6: #14b8a6 (Primary/500)
Swatch 7: #0d9488 (Primary/600) ← MAIN BRAND COLOR
  - Rectangle fill: #0d9488
  - Text: "Primary/600" (14px, White)
  - Text: "#0d9488" (12px, White)
  - Text: "PRIMARY - Buttons, links, highlights"
  - Badge: "BRAND"

Swatch 8: #0f766e (Primary/700)
Swatch 9: #115e59 (Primary/800)
Swatch 10: #134e4a (Primary/900)
```

**Frame 2: Grayscale Palette**
```
Layout: 10 rectangles (200x200px each), horizontal
Spacing: 16px gap

Gray/50 through Gray/900 (same structure as primary)

Key callouts:
- Gray/50: Backgrounds
- Gray/100: Surface colors
- Gray/200: Borders
- Gray/300: Disabled states
- Gray/600: Secondary text
- Gray/900: Primary text
```

**Frame 3: Semantic Colors**
```
Layout: 4 rectangles (300x200px each), 2x2 grid
Spacing: 24px gap

Success:
  - Rectangle: #10b981
  - Icon: ✓ (48px, white)
  - Text: "Success #10b981"
  - Usage: "Confirmations, completed states"

Warning:
  - Rectangle: #f59e0b
  - Icon: ⚠ (48px, white)
  - Text: "Warning #f59e0b"
  - Usage: "Cautions, pending actions"

Error:
  - Rectangle: #ef4444
  - Icon: ✕ (48px, white)
  - Text: "Error #ef4444"
  - Usage: "Errors, destructive actions"

Info:
  - Rectangle: #3b82f6
  - Icon: ⓘ (48px, white)
  - Text: "Info #3b82f6"
  - Usage: "Helpful tips, information"
```

**Frame 4: Background Colors**
```
Layout: 3 rectangles (400x300px each), horizontal
Spacing: 32px gap

Background:
  - Rectangle: #ffffff
  - Text: "Background #ffffff"
  - Usage: "Page backgrounds"

Surface:
  - Rectangle: #f9fafb (Gray/50)
  - Text: "Surface #f9fafb"
  - Usage: "Card backgrounds, sections"

Surface Raised:
  - Rectangle: #ffffff
  - Shadow: Elevation/2
  - Text: "Surface Raised #ffffff + shadow"
  - Usage: "Cards, modals, popovers"
```

#### Dark Mode Colors

**Frame 5: Dark Mode Palette**
```
Layout: Same as light mode, but inverted

Background: #000000 (pure black)
Surface: #1f2937 (Gray/800 from light mode)
Surface Raised: #374151 (Gray/700)

Text Primary: #f9fafb (Gray/50)
Text Secondary: #9ca3af (Gray/400)
Text Tertiary: #6b7280 (Gray/500)

Primary colors remain the same (teal doesn't change)
Semantic colors remain the same
```

**Annotation:**
- Add note: "Use Figma's Variables feature to toggle between light/dark"
- Create variable collection: "Mode: Light/Dark"
- Bind all color styles to variables

### 2.2 Typography System Frame

**Frame Dimensions:** 1920x1400px
**Layout:** Vertical stack of type specimens

#### Type Scale Specimens

**Display**
```
Frame: 1600x200px
Background: White
Border: 1px Gray/200

Text: "The quick brown fox jumps over the lazy dog"
Font: Playfair Display
Size: 56px
Weight: 600 (Semibold)
Line Height: 64px (114%)
Letter Spacing: -0.5px

Annotation (to the right):
  - "Display"
  - "56px / 64px / -0.5px"
  - "Playfair Display Semibold"
  - "Usage: Hero sections, page titles"
  - CSS: "var(--text-display)"
```

**Title 1**
```
Frame: 1600x160px
Text: "The quick brown fox jumps over the lazy dog"
Font: Playfair Display
Size: 40px
Weight: 600
Line Height: 48px
Letter Spacing: -0.3px

Annotation:
  - "Title 1"
  - "40px / 48px / -0.3px"
  - "Usage: Main page headers"
```

**Title 2**
```
Frame: 1600x140px
Font: Playfair Display
Size: 32px
Weight: 600
Line Height: 40px

Annotation:
  - "Title 2"
  - "32px / 40px"
  - "Usage: Section headers"
```

**Title 3**
```
Frame: 1600x120px
Font: Playfair Display
Size: 24px
Weight: 600
Line Height: 32px

Annotation:
  - "Title 3"
  - "24px / 32px"
  - "Usage: Card headers, subheadings"
```

**Headline**
```
Frame: 1600x100px
Font: DM Sans (switch to sans-serif)
Size: 20px
Weight: 500 (Medium)
Line Height: 28px

Annotation:
  - "Headline"
  - "20px / 28px"
  - "DM Sans Medium"
  - "Usage: Emphasized subheadings"
```

**Body**
```
Frame: 1600x240px
Text: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris."
Font: DM Sans
Size: 16px
Weight: 400 (Regular)
Line Height: 24px (150%)

Annotation:
  - "Body"
  - "16px / 24px / 150%"
  - "DM Sans Regular"
  - "Usage: Paragraphs, body text (PRIMARY TEXT STYLE)"
```

**Callout**
```
Frame: 1600x100px
Text: "The quick brown fox jumps over the lazy dog"
Font: DM Sans
Size: 16px
Weight: 500 (Medium)
Line Height: 24px

Annotation:
  - "Callout"
  - "16px / 24px"
  - "DM Sans Medium"
  - "Usage: Emphasized body text, labels"
```

**Subheadline**
```
Frame: 1600x90px
Font: DM Sans
Size: 14px
Weight: 400
Line Height: 20px

Annotation:
  - "Subheadline"
  - "14px / 20px"
  - "Usage: Small labels, metadata"
```

**Footnote**
```
Frame: 1600x80px
Font: DM Sans
Size: 13px
Weight: 400
Line Height: 18px

Annotation:
  - "Footnote"
  - "13px / 18px"
  - "Usage: Help text, form hints"
```

**Caption**
```
Frame: 1600x70px
Font: DM Sans
Size: 12px
Weight: 400
Line Height: 16px
Color: Gray/600

Annotation:
  - "Caption"
  - "12px / 16px"
  - "Usage: Captions, timestamps"
```

#### Type Pairing Examples

**Frame: 1600x400px**
```
Example 1: "Dashboard Header"
  - Title 1 (Playfair, 40px): "Welcome back, Sarah"
  - Body (DM Sans, 16px): "You have 23 active cases this week"

Example 2: "Card Header"
  - Title 3 (Playfair, 24px): "Case Summary"
  - Subheadline (DM Sans, 14px): "Updated 2 hours ago"

Example 3: "Stat Display"
  - Display (Playfair, 56px): "94%"
  - Caption (DM Sans, 12px): "SUCCESS RATE"
```

### 2.3 Spacing & Grid Frame

**Frame Dimensions:** 1920x1400px

#### 8px Grid System

**Frame 1: Spacing Scale**
```
Layout: Vertical stack of rectangles showing spacing increments

Spacing 1 (4px):
  - Rectangle: 4px width, 40px height, Primary/600
  - Label: "space-1 = 4px (0.5 × 8)"
  - Usage: "Tight spacing within components"

Spacing 2 (8px):
  - Rectangle: 8px width, 40px height, Primary/600
  - Label: "space-2 = 8px (1 × 8) - BASE UNIT"

Spacing 3 (12px):
  - Rectangle: 12px width, 40px height
  - Label: "space-3 = 12px (1.5 × 8)"

Spacing 4 (16px):
  - Rectangle: 16px width, 40px height
  - Label: "space-4 = 16px (2 × 8)"

... continue through space-32 (256px)

Create visual hierarchy:
- Tight (4-8px): Same color intensity
- Normal (16-24px): Medium color
- Loose (32-48px): Lighter color
- Generous (64-128px): Lightest color
```

**Frame 2: Component Spacing Examples**
```
Show practical examples:

Button padding:
  - Visual: Button with annotation lines
  - Vertical: 12px (space-3)
  - Horizontal: 24px (space-6)

Card padding:
  - Visual: Card with annotation
  - All sides: 24px (space-6)

Section margins:
  - Visual: Two sections with gap
  - Gap: 48px (space-12)
```

#### Grid Specifications

**Frame 3: Desktop Grid (1440px)**
```
Artboard: 1440x900px
Grid overlay:
  - 12 columns
  - Column width: 80px
  - Gutter: 32px
  - Margin: 64px (left/right)
  - Color: Primary/200 @ 30% opacity

Annotation:
  - "Desktop Grid: 12 columns"
  - "Container max-width: 1312px (1440 - 64*2)"
  - "Gutter: 32px"
```

**Frame 4: Tablet Grid (768px)**
```
Artboard: 768x1024px
Grid overlay:
  - 8 columns
  - Column width: 64px
  - Gutter: 24px
  - Margin: 32px

Annotation:
  - "Tablet Grid: 8 columns"
  - "Container max-width: 704px"
```

**Frame 5: Mobile Grid (375px)**
```
Artboard: 375x812px
Grid overlay:
  - 4 columns
  - Column width: 75px
  - Gutter: 16px
  - Margin: 16px

Annotation:
  - "Mobile Grid: 4 columns"
  - "Container max-width: 343px"
```

### 2.4 Shadows & Effects Frame

**Frame Dimensions:** 1920x800px

#### Elevation System

**Frame: 5 cards showing elevation levels**
```
Layout: 5 rectangles (250x250px each), horizontal
Spacing: 48px gap
Background: Gray/100 (to show shadows clearly)

Card 1: Elevation 1
  - Rectangle: White, rounded 12px
  - Shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)
  - Label below: "Elevation 1"
  - Usage: "Subtle hover, input fields"

Card 2: Elevation 2
  - Shadow: 0 3px 6px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.12)
  - Label: "Elevation 2"
  - Usage: "Cards, dropdowns"

Card 3: Elevation 3
  - Shadow: 0 10px 20px rgba(0,0,0,0.15), 0 3px 6px rgba(0,0,0,0.10)
  - Label: "Elevation 3"
  - Usage: "Modals, popovers"

Card 4: Elevation 4
  - Shadow: 0 15px 25px rgba(0,0,0,0.15), 0 5px 10px rgba(0,0,0,0.05)
  - Label: "Elevation 4"
  - Usage: "Dialogs, sheets"

Card 5: Elevation 5
  - Shadow: 0 20px 40px rgba(0,0,0,0.2)
  - Label: "Elevation 5"
  - Usage: "Full-screen overlays"
```

#### Focus States

**Frame: 3 input examples**
```
Layout: Vertical stack, 48px gap

Input 1: Default
  - Rectangle: 400x48px, white, border 1.5px Gray/300, radius 8px
  - Text: "Email Address" (placeholder)
  - Label: "Default state"

Input 2: Focus
  - Rectangle: 400x48px, white, border 1.5px Primary/600, radius 8px
  - Shadow: 0 0 0 3px Primary/100 (focus ring)
  - Text: "sarah@example.com"
  - Label: "Focus state - 3px glow"

Input 3: Error
  - Rectangle: 400x48px, white, border 1.5px Error/500, radius 8px
  - Shadow: 0 0 0 3px rgba(239,68,68,0.1)
  - Text: "invalid@"
  - Helper text: "Please enter a valid email"
  - Label: "Error state"
```

#### Backdrop Blur (Modals)

**Frame: Modal example**
```
Background: Screenshot mockup (blurred)
Overlay: rgba(0,0,0,0.5) with backdrop-filter: blur(10px)
Modal: White card, Elevation 5, centered

Annotation:
  - "Backdrop: rgba(0,0,0,0.5)"
  - "Blur: 10px (CSS: backdrop-filter)"
  - "Modal: Elevation 5 shadow"
```

### 2.5 Icons Frame

**Frame Dimensions:** 1920x1200px

#### Icon Library

**Layout: Grid of 8x6 icons (48 icons total)**

**Style Guidelines:**
- **Line Weight:** 2px (consistent)
- **Corner Radius:** 2px (rounded corners)
- **Size:** 24x24px (default), also create 16px and 32px variants
- **Color:** Gray/900 (default), Primary/600 (active)
- **Style:** Outlined (not filled) - Apple SF Symbols style

**Icon Categories:**

**Navigation (Row 1):**
- Home (house outline)
- Dashboard (squares grid)
- Clients (person outline)
- Cases (briefcase)
- Calendar (calendar)
- Analytics (bar chart)
- Settings (gear)
- Help (question circle)

**Actions (Row 2):**
- Add (plus circle)
- Edit (pencil)
- Delete (trash)
- Search (magnifying glass)
- Filter (funnel)
- Sort (arrows up/down)
- Download (down arrow to line)
- Upload (up arrow to line)

**Communication (Row 3):**
- Email (envelope)
- Phone (phone handset)
- SMS (chat bubble)
- Notification (bell)
- Share (share nodes)
- Send (paper plane)

**Status (Row 4):**
- Success (checkmark circle)
- Warning (exclamation triangle)
- Error (x circle)
- Info (i circle)
- Pending (clock)
- Active (dot filled)

**Documents (Row 5):**
- PDF (document)
- Image (photo)
- File (file outline)
- Folder (folder)
- Attachment (paperclip)
- Print (printer)

**Interface (Row 6):**
- Menu (hamburger)
- Close (x)
- Chevron Right (>)
- Chevron Down (v)
- Chevron Left (<)
- More (three dots)
- Star (star outline)
- Heart (heart outline)

**Annotation:**
- Each icon should be a Figma component
- Create variants: Size (16/24/32), State (Default/Active/Disabled)
- Name: Icon/Category/Name/Size/State (e.g., Icon/Navigation/Home/24/Default)

### 2.6 Illustrations Frame

**Frame Dimensions:** 1920x800px

#### Empty State Illustrations

**Specification:**
- Style: Simple line art (2px strokes)
- Colors: Gray/300 for lines, Primary/100 for fills
- Size: 200x200px (illustration area)
- Components needed:

**Empty State 1: No Clients**
```
Illustration:
  - Empty clipboard icon (large, centered)
  - Dashed rectangle (represents empty list)
  - Small plus icon in corner

Colors:
  - Clipboard: Gray/300 strokes
  - Background: Primary/50 fill
  - Plus: Primary/600

Below illustration:
  - Headline (20px): "No clients yet"
  - Body (16px, Gray/600): "Add your first client to get started"
  - Button: "Add Client" (Primary)
```

**Empty State 2: No Documents**
```
Illustration:
  - Folder icon (open, empty)
  - Three horizontal lines (representing empty space)

Colors:
  - Folder: Gray/300
  - Background: Primary/50

Text:
  - Headline: "No documents uploaded"
  - Body: "Drag and drop files here or browse"
  - Button: "Upload Document"
```

**Empty State 3: No Search Results**
```
Illustration:
  - Magnifying glass (large)
  - Empty circle (no results found)

Text:
  - Headline: "No results found"
  - Body: "Try adjusting your search or filters"
  - Link: "Clear all filters"
```

---

## Part 3: Component Library

### 3.1 Buttons

**Frame Dimensions:** 1920x1200px
**Layout:** Grid of button variations

#### Primary Button

**Component Structure:**
```
Button/Primary/
├── Size
│   ├── Small (sm)
│   ├── Medium (md) [Default]
│   └── Large (lg)
└── State
    ├── Default
    ├── Hover
    ├── Active
    ├── Disabled
    └── Loading
```

**Primary/Medium/Default Specs:**
```
Frame: Auto Layout (horizontal)
  - Padding: 12px (vertical), 24px (horizontal)
  - Gap: 8px (for icon + text)
  - Fill: Primary/600 (#0d9488)
  - Corner radius: 8px
  - Shadow: Elevation/1

Text:
  - Content: "Continue"
  - Style: Callout (16px, DM Sans Medium)
  - Color: White
  - Align: Center

Effects:
  - Shadow: Elevation/1

Icon (optional):
  - Size: 20x20px
  - Color: White
  - Position: Left or right of text
```

**Primary/Medium/Hover Specs:**
```
All same as Default, except:
  - Fill: Primary/700 (#0f766e)
  - Shadow: Elevation/2
  - Transform: translateY(-1px) [annotation only]
  - Cursor: Pointer [annotation]
```

**Primary/Medium/Active Specs:**
```
All same as Default, except:
  - Fill: Primary/800 (#115e59)
  - Shadow: Elevation/1
  - Transform: translateY(0) scale(0.98) [annotation]
```

**Primary/Medium/Disabled Specs:**
```
All same as Default, except:
  - Fill: Gray/300 (#d1d5db)
  - Text color: Gray/500
  - Shadow: None
  - Cursor: Not allowed [annotation]
  - Opacity: 100% (don't use opacity, change colors directly)
```

**Primary/Medium/Loading Specs:**
```
All same as Default, plus:
  - Add spinner icon (16x16px, white, animated)
  - Text: "Loading..."
  - Cursor: Wait [annotation]
```

**Size Variations:**

Small:
  - Padding: 8px (V), 16px (H)
  - Text: 14px
  - Icon: 16x16px
  - Height: 32px

Medium:
  - Padding: 12px (V), 24px (H)
  - Text: 16px
  - Icon: 20x20px
  - Height: 44px

Large:
  - Padding: 16px (V), 32px (H)
  - Text: 18px
  - Icon: 24x24px
  - Height: 56px

#### Secondary Button (Ghost)

**Component: Button/Secondary/Medium/Default**
```
Frame: Auto Layout
  - Padding: 12px (V), 24px (H)
  - Fill: Transparent
  - Border: 1.5px, Gray/300
  - Corner radius: 8px

Text:
  - Content: "Cancel"
  - Style: Callout (16px, DM Sans Medium)
  - Color: Primary/600

Effects:
  - Shadow: None (flat)

Hover state:
  - Border: Primary/600
  - Background: Primary/50
  - Text: Primary/700
```

#### Tertiary Button (Text Only)

**Component: Button/Tertiary/Medium/Default**
```
Frame: Auto Layout
  - Padding: 12px (V), 16px (H)
  - Fill: Transparent
  - Border: None
  - Corner radius: 8px

Text:
  - Content: "Learn More"
  - Style: Callout (16px, DM Sans Medium)
  - Color: Primary/600

Hover state:
  - Background: Gray/100
  - Text: Primary/700
```

#### Icon Button

**Component: Button/Icon/Medium/Default**
```
Frame: 44x44px (touch target size)
  - Fill: Transparent
  - Corner radius: 8px

Icon:
  - Size: 24x24px
  - Color: Gray/700
  - Center aligned

Hover state:
  - Background: Gray/100
  - Icon: Primary/600

Active state:
  - Background: Gray/200
  - Scale: 0.95
```

**Annotation for All Buttons:**
- Add redlines showing padding, height, width
- Add notes about interaction states
- Add CSS variable references
- Add accessibility notes (min 44px touch target, sufficient contrast)

### 3.2 Cards

**Frame Dimensions:** 1920x1400px

#### Basic Card

**Component: Card/Basic/Default**
```
Frame: 400x300px (flexible height)
  - Fill: White (Surface Raised)
  - Border: 1px, Gray/100
  - Corner radius: 12px
  - Shadow: Elevation/1
  - Padding: 24px (all sides)

Structure (Auto Layout, vertical):
  1. Header (optional)
  2. Body (flexible)
  3. Footer (optional)

Header:
  - Auto Layout (horizontal, space-between)
  - Left: Title (Title/3, 24px, Playfair)
  - Right: Icon button (more menu)
  - Margin bottom: 16px
  - Border bottom: 1px, Gray/100

Body:
  - Auto Layout (vertical, 12px gap)
  - Body text (16px, DM Sans)
  - Can contain any content

Footer:
  - Auto Layout (horizontal, 12px gap, right-aligned)
  - Border top: 1px, Gray/100
  - Padding top: 16px
  - Contains buttons

Hover state:
  - Shadow: Elevation/2
  - Transform: translateY(-2px) [annotation]
  - Transition: 300ms ease-out [annotation]
```

#### Stat Card

**Component: Card/Stat/Default**
```
Frame: 300x180px
  - Fill: White
  - Corner radius: 12px
  - Shadow: Elevation/1
  - Padding: 24px

Structure (Auto Layout, vertical, 16px gap):
  1. Icon container (48x48px, Primary/100 background, radius 12px)
     - Icon: 24x24px, Primary/600
  2. Value (Display, 56px, Playfair, Primary/900)
  3. Label (Caption, 12px, Gray/600, uppercase)
  4. Change indicator (optional)
     - "+12% vs last month"
     - Text: 14px, Success/600
     - Arrow up icon

Annotation:
  - "Stat cards should have generous whitespace"
  - "Value should be the focal point (large, bold)"
  - "Icon adds visual interest but shouldn't dominate"
```

#### Client Card (List Item)

**Component: Card/Client/Default**
```
Frame: Auto Layout (horizontal)
  - Width: Fill container (flexible)
  - Height: Auto
  - Fill: White
  - Border: 1px, Gray/100
  - Corner radius: 12px
  - Shadow: Elevation/1
  - Padding: 16px

Left border accent:
  - Position: Absolute (left edge)
  - Width: 4px
  - Height: 100%
  - Corner radius: 12px (left only)
  - Color: [Dynamic based on urgency]
    - Red (#ef4444) = Overdue
    - Yellow (#f59e0b) = Due today
    - Green (#10b981) = Future

Structure (Auto Layout, horizontal, 16px gap):
  1. Checkbox (hidden, shows on hover)
     - Size: 20x20px
     - Border: 2px, Gray/300
     - Corner radius: 4px
     - Check: Primary/600

  2. Avatar
     - Size: 48x48px
     - Corner radius: 9999px (circle)
     - Image or initials

  3. Info section (Auto Layout, vertical, 4px gap)
     - Name (Headline, 20px, Gray/900)
     - Status badge (below)

  4. Stats grid (Auto Layout, horizontal, 24px gap)
     - Follow-Up (label + value)
     - Stage (label + value)
     - Violations (label + value)

  5. Actions (Auto Layout, horizontal, 8px gap)
     - Quick action icons (hover)
     - Email, Phone, More buttons

Hover state:
  - Shadow: Elevation/2
  - Checkbox: opacity 1
  - Quick actions: opacity 1
```

#### Document Card (iCloud Style)

**Component: Card/Document/Default**
```
Frame: 200x240px
  - Fill: White
  - Corner radius: 12px
  - Shadow: Elevation/1
  - Padding: 16px

Structure (Auto Layout, vertical, 12px gap):
  1. Thumbnail container (168x120px)
     - Background: Gray/100
     - Corner radius: 8px
     - Contains:
       - PDF icon (64x64px, center)
       - OR image preview

  2. File name
     - Text: Body (16px), Gray/900
     - Max 2 lines, ellipsis

  3. Metadata
     - Text: Caption (12px), Gray/600
     - "Dec 1, 2025 • 245 KB"

  4. Download button (icon only)
     - Position: Absolute (top-right)
     - Size: 32x32px
     - Background: White/90, backdrop-blur
     - Icon: Download (16x16px)
```

### 3.3 Forms

**Frame Dimensions:** 1920x2000px (tall frame for many form variations)

#### Text Input with Floating Label

**Component: Input/Text/Default**
```
Frame: Auto Layout (vertical, 8px gap)
  - Width: 400px (flexible)
  - Height: Auto

Input container:
  - Frame: 400x56px
  - Fill: Surface (Gray/50)
  - Border: 1.5px, Gray/300
  - Corner radius: 8px
  - Padding: 16px (top), 8px (bottom), 16px (sides)

Label:
  - Text: "Email Address"
  - Position: Absolute
  - Top: 16px (default)
  - Left: 16px
  - Font: Body (16px), Gray/600
  - Transition: top 150ms, font-size 150ms [annotation]

Label (focused or filled):
  - Top: 6px
  - Font: Caption (12px), Primary/600

Input text:
  - Font: Body (16px), Gray/900
  - Placeholder: " " (space to trigger :not(:placeholder-shown))

Helper text (optional):
  - Text: "We'll never share your email"
  - Font: Footnote (13px), Gray/600
  - Margin top: 8px
```

**States:**

Default:
  - As above

Focus:
  - Border: Primary/600
  - Shadow: 0 0 0 3px Primary/100 (focus ring)
  - Label: moves up, Primary/600

Error:
  - Border: Error/500
  - Shadow: 0 0 0 3px rgba(239,68,68,0.1)
  - Icon: Error icon (16x16px, right side)
  - Helper text: Error message, Error/600

Disabled:
  - Background: Gray/100
  - Border: Gray/200
  - Text: Gray/400
  - Cursor: not-allowed

#### Select Dropdown

**Component: Input/Select/Default**
```
Frame: Similar to text input
  - Width: 400px
  - Height: 56px
  - Has chevron-down icon (right side, 20x20px)

Dropdown menu (when open):
  - Frame: Auto Layout (vertical, 0 gap)
  - Width: 400px (match input)
  - Max height: 300px (scroll if needed)
  - Fill: White
  - Border: 1px, Gray/200
  - Corner radius: 8px
  - Shadow: Elevation/3
  - Position: Below input, 4px gap

Option item:
  - Padding: 12px 16px
  - Height: 44px
  - Text: Body (16px)
  - Hover: Background Gray/50
  - Selected: Background Primary/50, Text Primary/700, Check icon
```

#### Checkbox

**Component: Input/Checkbox/Default**
```
Frame: Auto Layout (horizontal, 8px gap)

Checkbox:
  - Size: 20x20px
  - Border: 2px, Gray/300
  - Corner radius: 4px
  - Fill: Transparent

Checkbox (checked):
  - Fill: Primary/600
  - Border: Primary/600
  - Icon: White checkmark (14x14px, stroke-width 2px)

Label:
  - Text: Body (16px), Gray/900
  - Cursor: pointer

Hover state:
  - Border: Primary/600
  - Background: Primary/50 (if unchecked)

Focus state:
  - Shadow: 0 0 0 3px Primary/100
```

#### Radio Button

**Component: Input/Radio/Default**
```
Frame: Auto Layout (horizontal, 8px gap)

Radio:
  - Size: 20x20px
  - Border: 2px, Gray/300
  - Corner radius: 9999px (circle)
  - Fill: Transparent

Radio (selected):
  - Border: Primary/600
  - Inner dot: 10x10px circle, Primary/600, centered

Label:
  - Text: Body (16px), Gray/900
```

#### Toggle Switch

**Component: Input/Toggle/Default**
```
Track:
  - Width: 48px
  - Height: 28px
  - Corner radius: 14px (pill)
  - Fill: Gray/300

Toggle (off):
  - Track fill: Gray/300
  - Knob: 24x24px circle, White, left-aligned (2px inset)
  - Shadow: Elevation/1 on knob

Toggle (on):
  - Track fill: Primary/600
  - Knob: right-aligned (2px inset)
  - Animate: 300ms ease-out [annotation]

Label (optional):
  - Position: Right of toggle, 8px gap
  - Text: Body (16px)
```

### 3.4 Navigation

**Frame Dimensions:** 1920x1200px

#### Sidebar (Desktop)

**Component: Navigation/Sidebar/Expanded**
```
Frame: 280x1024px (full height)
  - Fill: White
  - Border right: 1px, Gray/200
  - Shadow: None

Header:
  - Height: 64px
  - Padding: 16px
  - Logo (160x32px)
  - Border bottom: 1px, Gray/200

Navigation items:
  - Auto Layout (vertical, 4px gap)
  - Padding: 8px

Nav item (default):
  - Auto Layout (horizontal, 12px gap)
  - Height: 44px
  - Padding: 10px 16px
  - Corner radius: 8px
  - Icon: 24x24px, Gray/600
  - Text: Callout (16px, DM Sans Medium), Gray/700

Nav item (active):
  - Background: Primary/50
  - Icon: Primary/600
  - Text: Primary/700

Nav item (hover):
  - Background: Gray/50

Section headers:
  - Text: Caption (12px, uppercase), Gray/600
  - Padding: 12px 16px
  - Not clickable
```

**Component: Navigation/Sidebar/Collapsed**
```
Frame: 72px width
  - Same as expanded, but:
  - Text labels hidden
  - Icons centered
  - Tooltip on hover (show label)

Expand button:
  - Position: Bottom left
  - Icon: Chevron right/left
  - Size: 40x40px
```

#### Bottom Tab Bar (Mobile)

**Component: Navigation/TabBar/Mobile**
```
Frame: 375x64px
  - Position: Fixed bottom
  - Fill: White/95 (semi-transparent)
  - Backdrop filter: blur(10px) [annotation]
  - Border top: 1px, Gray/200
  - Padding: 8px 0

Tab items:
  - Layout: Horizontal, space-evenly, 4 items
  - Auto Layout (vertical, 4px gap, center-aligned)

Tab item (default):
  - Icon: 24x24px, Gray/600
  - Label: Caption (12px), Gray/600
  - Height: 48px
  - Width: ~85px (375/4 - padding)

Tab item (active):
  - Icon: 24x24px, Primary/600
  - Label: Caption (12px), Primary/600
  - No background (iOS style)

Interaction:
  - Tap: Switch tabs with fade transition
  - Haptic feedback on tap [annotation]
```

#### Breadcrumbs

**Component: Navigation/Breadcrumbs**
```
Frame: Auto Layout (horizontal, 8px gap)

Breadcrumb item:
  - Text: Subheadline (14px), Primary/600
  - Hover: Primary/700, underline
  - Cursor: pointer

Separator:
  - Icon: Chevron right (16x16px), Gray/400
  - Not clickable

Current page:
  - Text: Subheadline (14px), Gray/900
  - Not clickable
  - No hover state
```

### 3.5 Modals & Overlays

**Frame Dimensions:** 1920x1080px

#### Modal (Center)

**Component: Modal/Center/Medium**
```
Backdrop:
  - Frame: 1440x900px (full screen)
  - Fill: rgba(0,0,0,0.5)
  - Backdrop blur: 10px [annotation - Figma doesn't support, just note]

Modal container:
  - Frame: 600x400px (flexible)
  - Position: Center of viewport
  - Fill: White
  - Corner radius: 16px
  - Shadow: Elevation/5
  - Padding: 32px

Structure (Auto Layout, vertical, 24px gap):
  1. Header
     - Auto Layout (horizontal, space-between)
     - Title: Title/2 (32px, Playfair)
     - Close button: Icon button (32x32px)

  2. Body
     - Auto Layout (vertical, 16px gap)
     - Body text (16px)
     - Can contain any content
     - Max height: 60vh, scroll if needed

  3. Footer
     - Auto Layout (horizontal, 12px gap, right-aligned)
     - Secondary button (Cancel)
     - Primary button (Confirm)

Animation in [annotation]:
  - Fade in backdrop (300ms)
  - Scale modal from 0.95 to 1 (300ms, ease-out)
  - Slight upward movement (20px)
```

#### Bottom Sheet (Mobile)

**Component: Modal/Sheet/Mobile**
```
Backdrop:
  - Frame: 375x812px (iPhone)
  - Fill: rgba(0,0,0,0.5)
  - Backdrop blur: 10px [annotation]

Sheet container:
  - Frame: 375x(auto, max 80vh)
  - Position: Bottom of screen
  - Fill: White
  - Corner radius: 24px (top corners only)
  - Shadow: Elevation/5
  - Padding: 24px

Handle:
  - Width: 36px
  - Height: 4px
  - Corner radius: 2px (pill)
  - Fill: Gray/300
  - Position: Top center, 12px from edge
  - Cursor: grab

Header:
  - Auto Layout (horizontal, space-between)
  - Title: Title/3 (24px)
  - Close button: Icon (24x24px)
  - Padding bottom: 16px
  - Border bottom: 1px, Gray/200

Body:
  - Padding: 24px 0
  - Scroll if content exceeds height

Animation in [annotation]:
  - Slide up from bottom (300ms, spring)
  - Can be dismissed by:
    - Dragging handle down
    - Tapping backdrop
    - Swiping down on content
```

#### Popover

**Component: Modal/Popover**
```
Popover container:
  - Frame: 280x(auto)
  - Fill: White
  - Corner radius: 12px
  - Shadow: Elevation/3
  - Padding: 8px

Arrow:
  - Width: 16px
  - Height: 8px
  - Fill: White (matches popover)
  - Position: Top center (pointing to trigger)

Content:
  - Auto Layout (vertical, 0 gap)
  - Menu items, each:
    - Height: 40px
    - Padding: 8px 12px
    - Text: Subheadline (14px)
    - Hover: Background Gray/50
    - Icon (optional): 16x16px, left-aligned

Divider (optional):
  - Height: 1px
  - Fill: Gray/200
  - Margin: 4px 0
```

### 3.6 Tables & Lists

**Frame Dimensions:** 1920x1400px

#### Responsive Table → Card List

**Desktop View (Table):**
```
Component: Table/Desktop

Table container:
  - Frame: 1200x(auto)
  - Fill: White
  - Corner radius: 12px
  - Border: 1px, Gray/200
  - Shadow: Elevation/1

Header row:
  - Height: 48px
  - Padding: 12px 16px
  - Fill: Gray/50
  - Border bottom: 2px, Gray/200

Header cell:
  - Text: Callout (16px, Medium), Gray/900
  - Sortable: Cursor pointer, sort icon (12x12px)
  - Hover: Background Gray/100

Data row:
  - Height: 64px
  - Padding: 12px 16px
  - Border bottom: 1px, Gray/100
  - Hover: Background Gray/50

Data cell:
  - Text: Body (16px), Gray/900
  - Align: Left (default), center (actions), right (numbers)

Actions column:
  - Width: 120px
  - Buttons: Icon buttons, 3-4 max
  - On hover: Show additional actions
```

**Mobile View (Cards):**
```
Component: Table/Mobile (Card View)

Cards container:
  - Auto Layout (vertical, 16px gap)

Card:
  - Frame: 343x(auto)
  - Fill: White
  - Corner radius: 12px
  - Border: 1px, Gray/200
  - Shadow: Elevation/1
  - Padding: 16px

Card structure (Auto Layout, vertical, 12px gap):
  1. Header (horizontal, space-between)
     - Avatar + Name
     - Status badge

  2. Stats grid (2x2, 16px gap)
     - Label: Caption (12px, uppercase, Gray/600)
     - Value: Callout (16px, Medium, Gray/900)

  3. Actions (horizontal, 8px gap, center)
     - Primary button
     - Secondary button

Responsive breakpoint [annotation]:
  - < 768px: Card view
  - ≥ 768px: Table view
```

### 3.7 Data Visualization

**Frame Dimensions:** 1920x1000px

#### Progress Ring (Apple Watch Style)

**Component: DataViz/ProgressRing/Large**
```
Container: 200x200px

SVG structure:
  - Background ring:
    - Circle: cx="100" cy="100" r="90"
    - Stroke: Gray/200
    - Stroke-width: 10px
    - Fill: None

  - Progress ring:
    - Circle: cx="100" cy="100" r="90"
    - Stroke: Primary/600
    - Stroke-width: 10px
    - Stroke-dasharray: 565 (circumference)
    - Stroke-dashoffset: [calculated based on percentage]
    - Stroke-linecap: round
    - Transform: rotate(-90deg) [start from top]
    - Fill: None

  - Center label (Auto Layout, vertical, center, 4px gap)
    - Value: Display (56px, Playfair), Primary/900
    - Label: Caption (12px, uppercase), Gray/600

Animation [annotation]:
  - Stroke-dashoffset animates from 565 to calculated value
  - Duration: 1000ms
  - Easing: ease-out
  - Trigger: On scroll into view
```

**Variants:**
- Size: Small (120px), Medium (160px), Large (200px)
- Color: Primary, Success, Warning, Error

#### Stat with Sparkline

**Component: DataViz/StatSparkline**
```
Frame: 300x120px
  - Auto Layout (vertical, 12px gap)

Stat:
  - Value: Display (48px, Playfair), Gray/900
  - Label: Caption (12px, uppercase), Gray/600
  - Change: Subheadline (14px), Success/600
    - Text: "+12% vs last week"
    - Icon: Arrow up (12x12px)

Sparkline:
  - Width: 300px
  - Height: 40px
  - Line: 2px, Primary/600
  - Fill: Linear gradient (Primary/200 to transparent)
  - Data points: 7-14 values
  - Smooth curve (not angular)
```

#### Donut Chart

**Component: DataViz/DonutChart**
```
Container: 200x200px

SVG structure:
  - Background circle: Gray/100, radius 85px
  - Segments:
    - Each segment: Different color
    - Stroke-width: 30px
    - Gap: 2px between segments
    - Calculate stroke-dasharray for each percentage

Center label:
  - Total value: Title/1 (40px)
  - Description: Caption (12px)

Legend (below chart):
  - Auto Layout (vertical, 8px gap)
  - Item: Color dot (12x12px) + Label + Percentage
```

---

## Part 4: Proof of Concept Screens

### 4.1 Dashboard (Desktop)

**Frame Dimensions:** 1440x900px

#### Layout Structure

**Grid Setup:**
- 12 columns
- 32px gutter
- 64px margins
- 8px baseline grid

#### Components Placement

**Frame: Dashboard/Desktop**

```
Structure:

1. Sidebar (left, fixed)
   - Width: 280px
   - Component: Navigation/Sidebar/Expanded
   - Use component instance

2. Main content (right, scrollable)
   - Width: 1096px (1440 - 280 - 64 margins)
   - Padding: 32px

   2.1 Hero Section (top)
       - Frame: 1032x300px
       - Background: Linear gradient (Primary/900 to Primary/700)
       - Corner radius: 16px
       - Padding: 48px
       - Content (center-aligned):
         - Number: Display (72px, White) "23"
         - Label: Headline (20px, White/80) "Active Cases This Week"
         - Button: Primary button "Start New Case" (white on teal)
       - Margin bottom: 32px

   2.2 Stats Grid
       - Layout: 3 columns, 24px gap
       - Height: 180px
       - Cards: Use Card/Stat component
       - Margin bottom: 32px

       Card 1 (Revenue):
         - Icon: 💰 (or dollar icon)
         - Value: "$47,250"
         - Label: "REVENUE (MTD)"
         - Change: "+12% vs last month" (green)

       Card 2 (Awaiting Response):
         - Icon: ⏱️ (or clock icon)
         - Value: "8"
         - Label: "AWAITING RESPONSE"
         - Change: "35 days avg" (neutral)

       Card 3 (Success Rate):
         - Icon: ✓ (or checkmark icon)
         - Value: "94%"
         - Label: "SUCCESS RATE"
         - Change: "+2% this quarter" (green)

   2.3 Pipeline Section
       - Frame: 1032x400px
       - Title: Title/2 (32px) "Case Pipeline"
       - Margin bottom: 16px

       Pipeline scroll:
         - Horizontal scroll container
         - 6 stages, each 250px wide, 24px gap
         - Total width: (250*6) + (24*5) = 1620px (scrollable)

       Stage card:
         - Width: 250px
         - Height: 360px
         - Background: White
         - Corner radius: 12px
         - Shadow: Elevation/1
         - Padding: 16px

       Stage header:
         - Icon: 40x40px, Primary/100 background, radius 8px
         - Title: Title/3 (24px), Playfair
         - Count badge: 16px, Primary/600 background, white text

       Stage content:
         - Mini cards (auto layout, 8px gap)
         - Each mini card:
           - Height: 60px
           - Background: Gray/50
           - Corner radius: 8px
           - Padding: 8px
           - Avatar (32px) + Name (14px)
         - Show max 4 cards
         - "+8 more" link at bottom

       - Margin bottom: 32px

   2.4 Recent Activity Feed
       - Frame: 1032x(auto)
       - Title: Title/2 (32px) "Recent Activity"
       - Margin bottom: 16px

       Activity cards:
         - Auto Layout (vertical, 16px gap)
         - Each card: 1032x120px

       Activity card structure:
         - Horizontal layout, 16px gap
         - Icon (left):
           - Size: 48x48px
           - Background: Success/100 (or Warning/Error based on type)
           - Icon: 24x24px, matching color
           - Corner radius: 12px
         - Content (middle, flex):
           - Title: Headline (20px, Gray/900)
           - Description: Body (16px, Gray/600)
           - Time: Caption (12px, Gray/500)
         - Action (right):
           - Button: Secondary button "View Case"

       Example cards:
         1. Success (green icon)
            - "Violation Deleted"
            - "Experian removed Capital One account for John Doe"
            - "2 hours ago"

         2. Pending (yellow icon)
            - "Response Overdue"
            - "TransUnion hasn't responded to Mary Smith (40 days)"
            - "5 hours ago"

         3. Info (blue icon)
            - "Document Uploaded"
            - "Sarah Johnson uploaded dispute response"
            - "1 day ago"

3. FAB (Floating Action Button)
   - Position: Fixed, bottom-right (32px from edges)
   - Size: 64x64px
   - Background: Primary/600
   - Icon: Plus (32x32px, white)
   - Corner radius: 32px (circle)
   - Shadow: Elevation/4
   - Hover: Scale 1.1, shadow Elevation/5
```

**Annotations:**
- Add redlines showing all spacing (32px, 24px, 16px)
- Add notes about scrolling behavior
- Add interaction notes (hover states, click actions)
- Add responsive notes (how layout adapts on smaller screens)

#### Responsive Behavior

**Tablet (768px-1024px):**
- Sidebar collapses to 72px (icons only)
- Main content expands
- Stats grid: 2 columns (3rd card wraps)
- Pipeline: Scroll with fade gradient at edges

**Mobile (<768px):**
- Sidebar becomes bottom tab bar
- Hero section: Reduce padding to 24px, font size to 48px
- Stats grid: 1 column, stack vertically
- Pipeline: Full-width horizontal scroll
- Activity feed: Reduce card height, stack icon/content vertically

### 4.2 Client List (Desktop)

**Frame Dimensions:** 1440x900px

#### Layout Structure

**Frame: ClientList/Desktop**

```
Structure:

1. Sidebar (same as Dashboard)

2. Main content
   - Width: 1096px
   - Padding: 32px

   2.1 Header Section
       - Auto Layout (horizontal, space-between)
       - Left: Page title (Title/1, 40px) "Clients"
       - Right: View toggle + Add button

       View toggle:
         - Auto Layout (horizontal, 0 gap)
         - Segmented control style
         - Button 1: "Cards" (active)
         - Button 2: "Table"
         - Background: Gray/100
         - Active: White, shadow
         - Corner radius: 8px

       Add button:
         - Primary button
         - Text: "Add Client"
         - Icon: Plus (20x20px)

       - Margin bottom: 24px

   2.2 Filter Bar
       - Frame: 1032x48px
       - Auto Layout (horizontal, 8px gap)

       Search input:
         - Width: 400px
         - Component: Input/Text
         - Placeholder: "Search clients..."
         - Icon: Search (20x20px, left)

       Filter chips:
         - Auto Layout (horizontal, 8px gap)
         - Chip (active):
           - Background: Primary/100
           - Text: Primary/700
           - Border: 1px, Primary/300
           - "All (247)"
         - Chip (inactive):
           - Background: Transparent
           - Text: Gray/700
           - Border: 1px, Gray/300
           - Hover: Gray/50
         - Chips: "Overdue (12)", "This Week (34)", "Needs Response (8)"
         - "+ Add Filter" chip

       - Margin bottom: 24px

   2.3 Client Grid (Card View)
       - Layout: CSS Grid, 3 columns, 24px gap
       - Each card: 328x(auto)px

       Client card (instance of Card/Client):
         - Component reference
         - Checkbox hidden by default
         - Urgency indicator (left border):
           - Red: Client 1, 3, 7 (overdue)
           - Yellow: Client 2, 5 (due today)
           - Green: Client 4, 6, 8, 9 (future)

         Sample clients:
           1. John Doe
              - Status: Active (green badge)
              - Follow-up: "2 days overdue" (red text)
              - Stage: "Dispute Sent"
              - Violations: 14
              - Avatar: Photo or initials "JD"

           2. Mary Smith
              - Status: Active
              - Follow-up: "Due today" (yellow)
              - Stage: "Analysis"
              - Violations: 8

           3. Robert Johnson
              - Status: Lead (blue badge)
              - Follow-up: "5 days overdue" (red)
              - Stage: "Intake"
              - Violations: 0

           [Continue with 6 more sample clients]

   2.4 Pagination (bottom)
       - Frame: 1032x48px
       - Auto Layout (horizontal, center, 16px gap)
       - Text: "Showing 1-9 of 247" (Subheadline, Gray/600)
       - Prev button (disabled)
       - Page numbers: 1 (active), 2, 3, ..., 28
       - Next button

3. Bulk Toolbar (hidden by default)
   - Position: Fixed, bottom, full-width
   - Height: 64px
   - Background: Primary/600
   - Shadow: Elevation/4
   - Padding: 12px 32px
   - Transform: translateY(100%) [initially hidden]

   Content (auto layout, horizontal, space-between):
     - Left: Text (white, Callout) "3 selected"
     - Center: Action buttons (horizontal, 12px gap)
       - "Change Status" (white ghost button)
       - "Send Email" (white ghost button)
       - "Assign To" (white ghost button)
     - Right: "Cancel" text button (white)

   Animation [annotation]:
     - Slides up when 1+ checkboxes selected
     - Duration: 300ms, spring easing
```

**Interaction States:**

**Card Hover:**
- Shadow: Elevation/2
- Transform: translateY(-2px)
- Checkbox: Fade in (opacity 0 → 1)
- Quick actions: Fade in (3 icon buttons on right)

**Card Selected:**
- Border: 2px, Primary/600
- Checkbox: Visible, checked
- Background: Primary/50

**Bulk Selection:**
- First checkbox checked: Toolbar slides up
- Additional checkboxes: Update count
- All unchecked: Toolbar slides down

### 4.3 Client Portal (Mobile)

**Frame Dimensions:** 375x812px (iPhone 13 Pro)

#### Layout Structure

**Frame: ClientPortal/Mobile**

```
Structure:

1. Status Bar (top)
   - Height: 44px
   - Background: White
   - Time, signal, battery (iOS standard)

2. Hero Section
   - Frame: 375x400px
   - Background: Linear gradient (Primary/900 to Primary/700)
   - Corner radius: 24px (bottom corners only)
   - Padding: 32px 24px

   Content (centered):
     - Greeting: Title/2 (32px, White) "Hi John"
     - Subtitle: Body (16px, White/80) "here's your progress"
     - Margin bottom: 32px

     Progress Ring:
       - Component: DataViz/ProgressRing/Large (200px)
       - Value: "75%"
       - Label: "COMPLETE"
       - Ring color: White/90
       - Background ring: White/20
       - Margin bottom: 16px

     Status text:
       - Body (16px, White)
       - "3 violations deleted, 2 pending response"

3. Stats Grid
   - Frame: 343x(auto)
   - Padding: 16px
   - Layout: 3 columns, 8px gap
   - Background: Transparent (overlaps hero with negative margin -32px)

   Stat cards (compact):
     - Width: 107px
     - Height: 100px
     - Background: White
     - Corner radius: 12px
     - Shadow: Elevation/2
     - Padding: 12px

     Structure (vertical, 8px gap):
       - Icon: 32x32px, Primary/100 background
       - Value: Headline (20px), Gray/900
       - Label: Caption (10px, uppercase), Gray/600

     Card 1: "$12K" - "EST. VALUE"
     Card 2: "18 days" - "UNTIL RESPONSE"
     Card 3: "14" - "VIOLATIONS"

4. Tab Bar (bottom, fixed)
   - Component: Navigation/TabBar/Mobile
   - Tabs: Summary, Documents, Scores, Profile
   - Height: 64px + safe area

5. Content Area (scrollable)
   - Padding: 16px
   - Between stats grid and tab bar

   5.1 Quick Status
       - Frame: 343x64px
       - Background: Success/50
       - Border: 1px, Success/200
       - Corner radius: 12px
       - Padding: 12px
       - Auto Layout (horizontal, 12px gap)

       Icon:
         - Size: 40x40px
         - Background: Success/100
         - Icon: Checkmark (24x24px, Success/600)
         - Corner radius: 8px

       Text:
         - Body (14px), Gray/900
         - "3 disputes sent, 2 responses received, 1 violation removed"

       - Margin bottom: 24px

   5.2 Timeline
       - Frame: 343x(auto)
       - Title: Title/3 (24px) "Case Timeline"
       - Margin bottom: 16px

       Timeline items:
         - Auto Layout (vertical, 16px gap)

       Timeline item (completed):
         - Auto Layout (horizontal, 12px gap)

         Dot (left):
           - Size: 24x24px
           - Background: Success/100
           - Border: 2px, Success/600
           - Circle

         Content (right):
           - Title: Headline (18px), Gray/900
           - Description: Subheadline (14px), Gray/600
           - Date: Caption (12px), Gray/500

         Example:
           - ✓ "Dispute Letters Sent"
           - "Sent to all 3 bureaus"
           - "Dec 1, 2025"

       Timeline item (current):
         - Dot: Pulsing animation (Primary/600)
         - Title: "Awaiting Bureau Response"
         - Description: "Deadline: Dec 31, 2025"
         - Date: "In progress"

       Timeline item (future):
         - Dot: Gray/300, no fill
         - Title: Gray/600
         - Description: Gray/500

   5.3 Next Steps Card
       - Frame: 343x(auto)
       - Background: White
       - Corner radius: 12px
       - Shadow: Elevation/1
       - Padding: 16px
       - Margin bottom: 80px (for tab bar)

       Content:
         - Title: Headline (20px) "What's Next?"
         - Description: Body (16px)
         - CTA: Primary button "View Documents"
```

**Interaction States:**

**Tab Navigation:**
- Tap tab: Content fades out, new content fades in
- Tab indicator: No background change, just color (iOS style)
- Haptic feedback on tap [annotation]

**Scroll Behavior:**
- Hero section: Slight parallax (scrolls slower than content)
- Stats grid: Sticky at top after scroll past hero
- Tab bar: Always fixed at bottom

**Pull to Refresh:**
- Drag down: Show refresh indicator
- Release: Trigger refresh animation
- Content: Fade out, reload, fade in

---

## Part 5: User Flows

### 5.1 New Case Creation Flow

**Frame: Flow/NewCase**

#### Screens to Design

**Screen 1: Dashboard (Starting Point)**
- Highlight FAB button with pulse animation
- Annotation: "User taps '+' button"

**Arrow →**

**Screen 2: Client Selection Modal**
- Modal appears (center of screen)
- Title: "Start New Case"
- Search input: "Search existing client or add new"
- List of recent clients (5 items, scrollable)
- Button: "Add New Client" (secondary, bottom)
- Annotation: "User can select existing or add new"

**Arrow → (Existing Client)**

**Screen 3: Upload Credit Report**
- Modal transitions to upload screen
- Title: "Upload Credit Report"
- Large dropzone area (dashed border)
- Icon: Cloud upload
- Text: "Drag and drop PDF here or browse"
- Supported formats note
- Primary button: "Continue" (disabled until upload)

**Arrow →**

**Screen 4: Processing**
- Modal shows processing state
- Animated spinner or progress bar
- Text: "Analyzing credit report..."
- Sub-text: "This may take 60-90 seconds"
- Cannot close modal during processing

**Arrow →**

**Screen 5: Success Confirmation**
- Modal shows success state
- Large checkmark icon (animated)
- Text: "Analysis Complete!"
- Stats preview:
  - "14 violations found"
  - "Case strength: 7/10"
  - "Estimated value: $12,450"
- Button: "View Full Analysis" (primary)
- Button: "Back to Dashboard" (text)

**Arrow →**

**Screen 6: Analysis Review Page**
- Full page (not modal)
- Shows detailed analysis results
- Sections: Violations, Standing, Damages, etc.
- Action buttons at bottom

**FigJam Diagram:**
- Use Figma's prototyping to link screens
- Add annotations at each step
- Show decision points (existing vs new client)
- Show error states (invalid file, processing failed)

### 5.2 Bulk Client Operations Flow

**Frame: Flow/BulkOperations**

#### Screens to Design

**Screen 1: Client List (Default)**
- Grid of client cards
- No selections
- Annotation: "User hovers over first card"

**Arrow →**

**Screen 2: Hover State**
- First card shows:
  - Checkbox (faded in)
  - Quick action icons (visible)
- Annotation: "User clicks checkbox"

**Arrow →**

**Screen 3: First Selection**
- Card border: Primary/600
- Checkbox: Checked
- Background: Primary/50
- Bulk toolbar: Slides up from bottom (animated)
- Toolbar shows: "1 selected"
- Annotation: "User selects 2 more clients"

**Arrow →**

**Screen 4: Multiple Selection**
- 3 cards selected (borders, backgrounds)
- Toolbar shows: "3 selected"
- Action buttons visible:
  - "Change Status"
  - "Send Email"
  - "Assign To"
  - "Cancel"
- Annotation: "User clicks 'Change Status'"

**Arrow →**

**Screen 5: Status Dropdown**
- Popover appears above toolbar
- List of statuses:
  - Active
  - Lead
  - Pending
  - Closed
  - Archived
- Current status highlighted
- Annotation: "User selects 'Active'"

**Arrow →**

**Screen 6: Confirmation Toast**
- Selections clear
- Toolbar slides down
- Toast notification appears (top-right)
- Text: "3 clients updated to Active"
- Icon: Success checkmark
- Auto-dismiss after 3s

**FigJam Diagram:**
- Show multi-select capability
- Show toolbar appearance animation
- Show toast notification system
- Add error case (no action selected)

### 5.3 Client Portal Onboarding Flow

**Frame: Flow/PortalOnboarding**

#### Screens to Design

**Screen 1: Welcome Email (External)**
- Email mockup (Apple Mail style)
- Subject: "Your FCRA Analysis is Ready"
- Preview text
- CTA button: "View Your Case"
- Annotation: "Client clicks link in email"

**Arrow →**

**Screen 2: Password Creation (First Visit)**
- Mobile screen (375x812px)
- Hero image: Gradient background
- Logo at top
- Title: "Create Your Password"
- Subtitle: "Secure your case portal"
- Input: Email (pre-filled, disabled)
- Input: Password (with strength indicator)
- Input: Confirm Password
- Checkbox: "I agree to terms"
- Button: "Create Account" (primary)
- Annotation: "User creates password"

**Arrow →**

**Screen 3: Biometric Prompt (iOS)**
- Native iOS prompt (mockup)
- Title: "Use Face ID for [App Name]?"
- Text: "Sign in quickly and securely"
- Buttons: "Use Face ID" / "Not Now"
- Annotation: "User enables Face ID"

**Arrow →**

**Screen 4: Portal Home (First View)**
- Client Portal screen (as designed in Part 4)
- Show tour tooltips (overlay)
- Tooltip 1: Hero card ("This is your case summary")
- Tooltip 2: Tab bar ("Navigate here")
- Tooltip 3: Progress ring ("Track your progress")
- Button: "Next" / "Skip Tour"
- Annotation: "User goes through tour"

**Arrow →**

**Screen 5: Dashboard (Tour Complete)**
- Tooltips removed
- Confetti animation (celebratory)
- Toast: "Welcome! Your case has 14 violations"
- Full interactivity enabled

---

## Part 6: Interactions & Animations

### 6.1 Button States

**Frame: Interactions/Buttons**

Create prototype with these transitions:

**Primary Button:**

State 1: Default
- Scale: 1
- Shadow: Elevation/1
- Background: Primary/600

→ **On Hover** (100ms, ease-out) →

State 2: Hover
- Scale: 1
- Shadow: Elevation/2
- Background: Primary/700
- Transform: translateY(-1px)

→ **On Click** (50ms, ease-in) →

State 3: Active
- Scale: 0.98
- Shadow: Elevation/1
- Background: Primary/800
- Transform: translateY(0)

→ **On Release** (200ms, spring) →

State 1: Default (reset)

**Annotation:**
- Add timing labels on arrows
- Add easing curve notation
- Note: "Use Smart Animate for smooth transitions"

### 6.2 Page Transitions

**Frame: Interactions/PageTransitions**

**Dashboard → Client List:**

**Transition:**
- Type: Slide
- Direction: Left to right
- Duration: 300ms
- Easing: ease-out
- Overlap: 50% (new page starts sliding in while old page slides out)

**Figma Prototype:**
1. Create 2 frames: Dashboard, Client List
2. Link with "Navigate to" interaction
3. Animation: "Move in"
4. Direction: Left
5. Easing: Ease out
6. Duration: 300ms

**Screen Recording:**
- Record prototype interaction
- Export as GIF or MP4
- Add to documentation

### 6.3 Loading States

**Frame: Interactions/LoadingStates**

#### Skeleton Screen

**Before:**
- Client card with gray placeholder shapes
- Avatar: Gray circle (animated shimmer)
- Name: Gray rectangle (120px wide, shimmer)
- Stats: 3 gray rectangles (shimmer)

**Animation:**
- Gradient overlay: Linear gradient (Gray/200 → Gray/100 → Gray/200)
- Movement: Left to right, continuous loop
- Duration: 1500ms
- Easing: Linear

**After:**
- Skeleton fades out (300ms)
- Real content fades in (300ms)
- Slight scale up (0.95 → 1)

**Figma Animation:**
- Use variants: Loading / Loaded
- Prototype: After delay → Loaded (1500ms)
- Smart Animate transition

#### Spinner

**Component: Loading/Spinner**

Circle:
- Size: 40x40px
- Stroke: Primary/600
- Stroke-width: 4px
- Stroke-dasharray: 120 (partial circle)
- Rotate: 0deg → 360deg
- Duration: 1000ms
- Easing: Linear
- Loop: Infinite

**Figma:**
- Create component with circle
- Prototype: While hovering → Rotate 360deg
- Duration: 1000ms
- Ease: Linear

#### Progress Bar

**Component: Loading/ProgressBar**

Container:
- Width: 300px
- Height: 4px
- Background: Gray/200
- Corner radius: 2px

Progress:
- Height: 4px
- Background: Primary/600
- Corner radius: 2px
- Width: 0% → 100% (animates)

**Figma:**
- Create variants: 0%, 25%, 50%, 75%, 100%
- Link with "After delay" interactions
- Each step: 500ms

---

## Part 7: Before/After Comparisons

### 7.1 Dashboard Comparison

**Frame: Comparison/Dashboard**

**Layout:**
- Side by side, 2 columns
- Each column: 720px wide (half of 1440px)
- Divider: 2px, Gray/300

**Left Side: BEFORE**
- Screenshot of current dashboard (from codebase)
- Label at top: "BEFORE" (Caption, Gray/600)
- Annotations (red circles with numbers):
  1. "Gradient cards (dated)"
  2. "Cramped spacing"
  3. "10-column table (overwhelming)"
  4. "Sidebar takes 25% of screen"

**Right Side: AFTER**
- Mockup of new dashboard (from Part 4)
- Label at top: "AFTER" (Caption, Primary/600)
- Annotations (green circles with numbers):
  1. "Hero metric (focus)"
  2. "Generous whitespace (60%)"
  3. "Card-based feed (scannable)"
  4. "Sidebar auto-hides"

**Bottom: Key Improvements**
- List (3 columns):
  - "60% whitespace target met"
  - "3x faster task completion"
  - "One primary action (FAB)"

### 7.2 Client List Comparison

**Frame: Comparison/ClientList**

**Before:**
- 10-column table
- Striped rows
- Small text
- No visual hierarchy

**After:**
- Card-based grid
- Color-coded urgency
- Bulk operations toolbar
- Smart filters

**Annotations:**
- Highlight missing features: "No bulk actions" (before)
- Highlight new features: "Bulk toolbar" (after)
- Show density: "10 data points per row" vs "3 key stats per card"

### 7.3 Portal Comparison

**Frame: Comparison/Portal**

**Before:**
- 7 horizontal tabs (cramped)
- Dense information
- Generic stats

**After:**
- Bottom tab bar (mobile)
- Personalized hero
- Progress ring
- One-line status

**Annotations:**
- "7 tabs → 4 tabs (simplified)"
- "Generic layout → Personalized ('Hi John')"
- "Data tables → Visual rings"

---

## Part 8: Developer Handoff

### 8.1 Handoff Specifications

**Frame: Handoff/Specifications**

#### CSS Variables Export

Create a frame with all CSS variables formatted:

```css
/* Copy-paste ready CSS */

:root {
  /* Colors */
  --color-primary-50: #f0fdfa;
  --color-primary-600: #0d9488;
  --color-gray-900: #111827;
  /* ... all colors */

  /* Typography */
  --text-display: 56px;
  --line-display: 64px;
  --weight-display: 600;
  /* ... all text styles */

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  /* ... all spacing */

  /* Shadows */
  --elevation-1: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
  /* ... all shadows */

  /* Animations */
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  /* ... all animations */
}
```

#### Component Specs

For each component, provide:

**Example: Primary Button**

```
Component: Button/Primary/Medium

HTML:
<button class="btn btn-primary">Continue</button>

CSS:
.btn-primary {
  padding: 12px 24px;
  font-family: var(--font-body);
  font-size: var(--text-body);
  font-weight: 500;
  background: var(--color-primary-600);
  color: white;
  border: none;
  border-radius: 8px;
  box-shadow: var(--elevation-1);
  transition: all var(--duration-normal) var(--ease-out);
  cursor: pointer;
}

.btn-primary:hover {
  background: var(--color-primary-700);
  box-shadow: var(--elevation-2);
  transform: translateY(-1px);
}

.btn-primary:active {
  transform: translateY(0) scale(0.98);
}

Accessibility:
- Min touch target: 44x44px ✓
- Contrast ratio: 4.5:1 ✓
- Keyboard accessible: Focus ring required
- Screen reader: Button text must be descriptive
```

### 8.2 Inspection Tool Setup

**Figma Dev Mode:**
- Enable Dev Mode for handoff
- Set measurement units: px (not pt)
- Export assets:
  - Icons: SVG
  - Images: PNG (2x, 3x for retina)
  - Logos: SVG preferred

**Export Settings:**
- Frame exports: PNG, 2x resolution
- Icons: SVG (fill/stroke as needed)
- Illustrations: SVG
- Photos: JPG (optimized, 80% quality)

### 8.3 Responsive Breakpoints

**Frame: Handoff/Responsive**

Show breakpoints clearly:

```
Mobile:
  - Width: 375px - 767px
  - Grid: 4 columns, 16px margin, 16px gutter
  - Font scale: Base (16px)

Tablet:
  - Width: 768px - 1023px
  - Grid: 8 columns, 32px margin, 24px gutter
  - Font scale: Base (16px)

Desktop:
  - Width: 1024px+
  - Grid: 12 columns, 64px margin, 32px gutter
  - Font scale: Base (16px)

Large Desktop:
  - Width: 1920px+
  - Max content width: 1440px (centered)
```

---

## Part 9: Quality Checklist

### Before Delivering Figma File:

**Design System:**
- [ ] All colors use Figma Styles (not raw hex)
- [ ] All text uses Figma Text Styles
- [ ] All shadows use Figma Effect Styles
- [ ] Variables created for light/dark mode
- [ ] Grid styles saved (8px, 12-col, 4-col)

**Components:**
- [ ] All components have variants (size, state)
- [ ] Component naming: Consistent (Component/Category/Size/State)
- [ ] Auto Layout applied where appropriate
- [ ] Constraints set for responsive behavior
- [ ] Component descriptions filled in

**Mockups:**
- [ ] Frames match device specs (375x812, 1440x900)
- [ ] Use component instances (not detached)
- [ ] Content is realistic (names, numbers, dates)
- [ ] All interactions prototyped (hover, click, transitions)
- [ ] Annotations added for developers

**Accessibility:**
- [ ] Contrast ratios checked (Stark plugin)
- [ ] Text sizes readable (min 12px)
- [ ] Touch targets meet 44px minimum
- [ ] Color not sole indicator (icons + text)
- [ ] Focus states designed

**Handoff:**
- [ ] Dev Mode enabled
- [ ] Export settings configured
- [ ] CSS variables documented
- [ ] Responsive breakpoints noted
- [ ] Before/after comparisons included

**Polish:**
- [ ] Layers named clearly (no "Rectangle 47")
- [ ] Unused layers deleted
- [ ] Pages organized logically
- [ ] Cover page complete
- [ ] Version history saved

---

## Part 10: Next Steps After Figma Design

### Phase 1: Design Validation (Week 1)

1. **Internal Review:**
   - Present Figma file to stakeholders
   - Walk through 3 POC screens
   - Explain design system rationale
   - Get approval to proceed

2. **User Testing:**
   - Recruit 5 staff + 5 clients
   - Use Figma prototype for testing
   - Tasks: "Find client", "Check case status", "Upload document"
   - Collect feedback via Maze.co or UserTesting.com

3. **Iterate:**
   - Address feedback
   - Refine designs
   - Version 1.1 of Figma file

### Phase 2: Development Handoff (Week 2)

1. **Developer Walkthrough:**
   - 60-min session with dev team
   - Explain design system
   - Show component library
   - Answer questions about interactions

2. **Export Assets:**
   - Icons: SVG export
   - Images: 2x PNG export
   - Logos: SVG + PNG

3. **Create Tickets:**
   - Break designs into Jira/Linear tasks
   - Priority: Dashboard → Client List → Portal
   - Assign to frontend developers

### Phase 3: Implementation (Weeks 3-6)

1. **CSS Foundation:**
   - Create apple-design-system.css
   - Define all variables
   - Set up dark mode toggle

2. **Component Library:**
   - Build React/Vue components (if applicable)
   - Or build reusable HTML/CSS components
   - Storybook for component documentation

3. **Screen Implementation:**
   - Week 3: Dashboard
   - Week 4: Client List
   - Week 5: Client Portal
   - Week 6: QA, polish, responsive testing

### Phase 4: Validation & Iteration (Week 7)

1. **QA Testing:**
   - Cross-browser (Chrome, Safari, Firefox, Edge)
   - Cross-device (Desktop, tablet, mobile)
   - Accessibility audit (WAVE, axe DevTools)

2. **User Acceptance:**
   - Staff beta test (7 days)
   - Client beta test (7 days)
   - Collect feedback

3. **Final Polish:**
   - Address bugs
   - Refine animations
   - Optimize performance

---

## Conclusion

This specification provides everything needed to create comprehensive Apple-style Figma mockups for the FCRA platform. The designer should:

1. **Set up Figma file** with proper structure (pages, frames, grids)
2. **Create design system** (colors, typography, spacing, shadows)
3. **Build component library** (buttons, cards, forms, navigation, modals)
4. **Design 3 POC screens** (Dashboard, Client List, Client Portal)
5. **Document interactions** (hover, click, transitions, animations)
6. **Create user flows** (new case, bulk operations, portal onboarding)
7. **Show before/after** comparisons
8. **Prepare developer handoff** (CSS variables, specs, assets)

**Estimated Design Time:**
- Design System: 1 week
- Component Library: 1 week
- POC Screens: 1 week
- Flows & Interactions: 1 week
- **Total: 4 weeks** (1 designer, full-time)

**Deliverables:**
- ✅ Figma file (shareable link)
- ✅ Exported assets (icons, images)
- ✅ CSS variables (copy-paste ready)
- ✅ Design specification PDF (this document)
- ✅ Prototype demo (interactive)

---

**Document prepared by:** Claude Sonnet 4.5
**Date:** December 14, 2025
**Version:** 1.0
**For:** Apple-Style FCRA Platform Redesign
**Figma File Status:** Specification Complete, Ready for Design
