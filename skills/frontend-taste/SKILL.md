---
name: frontend-taste
description: Enforces custom, high-end frontend design directions (Editorial, Brutalist, Premium Luxury) and bans generic AI-generated styles.
---

# frontend-taste (Break the Default UI/UX)

This skill overrides default, generic AI design tendencies. Neural networks default to "average" design choices (e.g., Inter font, `rounded-lg` buttons, generic white backgrounds with purple gradients). This skill forces distinct, high-fidelity design directions.

## Design Styles

When starting a UI task, select **exactly one** of these three directions and commit to it globally.

### 1. Editorial (Classic & Literary)
Best for portfolios, blogs, marketing sites, and high-end services.
*   **Typography**: Serif font for headings (`font-serif`), clean sans-serif for body.
*   **Spacing**: High breathing room, asymmetrical layouts, large margins.
*   **Colors**: High contrast, warm backgrounds (cream, beige), slate or dark brown text.
*   **Tailwind presets**:
    *   Headings: `font-serif tracking-tight text-slate-900 font-normal`
    *   Cards: `border-b border-slate-200 py-8 first:pt-0` (no shadow, no border-radius)
    *   Buttons: `border border-slate-900 px-6 py-2 hover:bg-slate-900 hover:text-white transition-colors duration-300`

### 2. Industrial Brutalist (Raw & Technical)
Best for developer tools, web3, analytics, and technical platforms.
*   **Typography**: Monospace font for headings and UI labels (`font-mono`), sans-serif for body.
*   **Layout**: Hard borders, prominent grids, visible lines, dark shadows without blur (neo-brutalism).
*   **Colors**: Neon accents (volt, cyan, hot pink), deep blacks, raw grays.
*   **Tailwind presets**:
    *   Headings: `font-mono uppercase tracking-wider text-black`
    *   Cards: `border-2 border-black bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] p-6`
    *   Buttons: `border-2 border-black bg-yellow-300 px-4 py-2 font-mono uppercase tracking-wider shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none transition-all duration-150`

### 3. Premium Luxury (Sleek & Editorial Dark)
Best for SaaS landing pages, B2B premium services, and high-conversion products.
*   **Typography**: Elegant sans-serif or clean serif, thin weights.
*   **Layout**: Balanced symmetry, thin borders, soft glowing gradients (glassmorphism).
*   **Colors**: Pitch black (`bg-[#030303]`), gold, silver, or very subtle indigo glows.
*   **Tailwind presets**:
    *   Headings: `font-sans font-light tracking-tight text-white/90`
    *   Cards: `bg-white/[0.02] border border-white/[0.05] rounded-2xl backdrop-blur-md`
    *   Buttons: `bg-white text-black px-6 py-3 rounded-full hover:bg-white/90 transition-colors`

---

## Whitelist & Blacklist

### 🚫 Blacklist (Never Use)
*   **No generic fonts**: Never default to `font-sans` (Inter) for everything without specifying weights and letter-spacing.
*   **No default shadows**: Do not use `shadow-md` or `shadow-lg` blindly. They look generic.
*   **No default border-radius**: Stop using `rounded-lg` on all cards and buttons. Use `rounded-none` (Brutalist), `rounded-full` (Premium), or borderless bottom lines (Editorial).
*   **No emoji icons**: Never use emojis (🚀, 🎨) as icons. Only SVG icons (Lucide or Heroicons).
*   **No purple-to-blue gradients**: Avoid the default "AI-SaaS" color scheme. Use specific brand-colors from `DESIGN.md` or UUPM.

### ✅ Whitelist (Always Use)
*   **Define design direction first**: Write a 1-sentence design statement in your draft before writing any code.
*   **Asymmetrical elements**: Break grids occasionally with 1/3 layouts or off-grid alignments.
*   **Micro-interactions**: Use `transition-all duration-300 ease-out` on all interactive states.
*   **Color palette discipline**: Restrict layout to 1 primary color, 1 neutral color, and 1 accent color maximum.
