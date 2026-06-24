---
name: website-cloning
description: Rules and steps for reverse-engineering, asset-harvesting, and cloning any website into clean Next.js/Tailwind code or static HTML/CSS templates.
---

# Website Cloning & Reverse-Engineering

This skill guides the process of copying the layout, design system, and assets of any target website, converting it into a clean frontend codebase.

## 🛠️ Requirements & Tools
- **Browser Automation**: Chrome DevTools MCP or Playwright MCP must be active to navigate the target website and inspect runtime computed styles.
- **Asset Downloader**: Bash utilities (`wget`, `curl`) for downloading images, media files, and fonts.
- **Styling Standards**: Tailwind CSS (v4 preferred) using oklch design tokens mapped from the target's style palette.

## 📐 Implementation Workflow

### 1. Reconnaissance & Style Extraction
1. Use browser automation to navigate to the target URL.
2. Take full-page screenshots at Desktop (1440px) and Mobile (390px) widths for visual reference.
3. Extract **Global Styles**:
   - Run JS in console to collect computed font families, weights, and sizes.
   - Run JS to extract the unique color palette (convert hex/rgb to CSS custom properties).
   - Locate and download the favicon, meta tags, and OpenGraph images.

### 2. Asset Harvesting
- **Images & Videos**: Scan the DOM for all `<img>` src paths, background-image URLs, and `<video>` tags. Download assets to `/public/assets/cloned/<domain>/`.
- **SVGs**: Extract inline `<svg>` elements and convert them into clean React components or static inline assets.
- **Layered Assets**: Inspect absolute overlays, grids, and background overlays. Never assume a section is a single image; dissect the stack.

### 3. Component Specification
Before writing code, create a specification document under `docs/research/<domain>/specs.md`:
- List each page section (Navbar, Hero, Features, Footer) with its computed padding, margin, flex/grid properties, and font styles.
- Document **Interaction Models**: Identify scroll-driven behaviors (sticky navs, fade-ups via IntersectionObserver), click actions (tab switching, modals), and hover transitions. Document timing and easing functions.

### 4. Code Construction
- **Foundation First**: Update global stylesheets with extracted design tokens. Map them to project design tokens (primary, background, foreground, secondary, muted).
- **Section-by-Section Rebuilding**: Rebuild the layout from top to bottom.
- **Style Discipline**: Use strictly utility classes (e.g. Tailwind). Never use hardcoded inline styles. Maintain responsiveness at all breakpoints.

## ⚠️ Common Pitfalls
- **Approximating Styles**: Guessing paddings, colors, and margins instead of checking computed styles (leads to visual misalignment). Always run `window.getComputedStyle(element)`.
- **Broken Interaction Models**: Implementing click tabs for a section that snaps on scroll or vice versa.
- **Missing Overlay Layers**: Forgetting foreground UI panels or absolute decals that were layered over a background.
