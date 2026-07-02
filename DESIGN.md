# Design System: Vibecode (Techno-Editorial Brutalism)

## 1. Visual Theme & Atmosphere
A high-contrast, structural interface inspired by premium design studios (like Craftwork) and modular synthesizer interfaces. The layout is built around a **visible 1px blueprint grid**—thin, semi-transparent lines that divide the screen into columns and rows. Content is anchored directly to this grid. The mood is raw, technical, and expensive.

- **Density:** 6 (Structured, high information density with sharp boundaries)
- **Variance:** 10 (Extreme asymmetry, overlapping text, off-grid elements)
- **Motion:** 8 (Snappy, spring-physics rotations, micro-glitches, and hover-triggered grid expansions)

## 2. Color Palette & Roles
- **Space Void** (#020204) — Pure dark void background
- **Raw Metal** (#08090c) — Dark container fills
- **Pure White** (#ffffff) — High-contrast display typography
- **Industrial Grey** (#71717a) — Muted label text and technical metadata
- **Grid Line** (rgba(255, 255, 255, 0.05)) — Visible 1px structural lines dividing sections
- **Electric Cyan** (#00f0ff) — High-voltage cyan accent, used strictly as a single laser beam for active states and critical CTAs.

*Strictly BANNED: Soft gradients, generic rounded cards, and neon drop shadows.*

## 3. Typography Rules
- **Display:** `Cabinet Grotesk` — Extremely thin (`font-weight: 100`), massive scale (`120px` on desktop), track-tight (`-0.05em`), mostly lowercase. 
  - *Signature Technique:* **Inline Typography Pill**. We embed small, highly styled pill-shaped 3D images directly inside the headlines as punctuation or letter replacements.
- **Body:** `Satoshi` — Weight 300, relaxed leading (1.7), 60ch max-width.
- **Mono:** `JetBrains Mono` — Used for all numbers, labels, logs, and code. Every number on the site (e.g., section counters, dates) must be monospace.
- **Banned:** `Inter`, generic system sans-serifs, and any generic serif fonts.

## 4. Layout & Grid (The Blueprint Grid)
- **The Visible Grid:** The entire page is structured by visible vertical and horizontal `1px` lines (`border-l`, `border-r`, `border-t`, `border-b` using `Grid Line` color).
- **Sharp Corners:** All content blocks, inputs, and terminals have **0px border-radius** (perfectly sharp corners). Only buttons and inline typography images can use **9999px pill shapes** to create a stark visual contrast.
- **Overlapping Elements:** Headings are allowed to slightly overlap grid borders or background visual elements to break the flat 2D plane.

## 5. Component Stylings
* **Buttons:** Perfectly flat, either solid Electric Cyan with black text, or a raw outline with sharp corners. On hover, they shift by `-2px` with a solid block shadow behind them (`box-shadow: 2px 2px 0px #00f0ff`).
* **Terminal Windows:** Darker fills (`#010102`), sharp 0px corners, surrounded by a 1px Grid Line. The top bar contains raw text tab labels (e.g., `bash`, `logs`) instead of generic colored dots.
* **Timeline (The Stack):** A vertical stack of full-width grid rows. Each step is separated by a horizontal `1px` Grid Line. Large monospace numbers (`01`, `02`, `03`) act as anchors.

## 6. Motion & Interaction
- **Snappy Spring:** Buttons and interactive tabs use a highly responsive spring (`stiffness: 180, damping: 12`) for instant tactile feedback.
- **Grid Expansion:** Hovering over a grid section slightly brightens the surrounding border lines.
- **Scanlines & Noise:** A subtle, fixed grain texture overlays the entire viewport to give it a physical, hardware-like feel.

## 7. Anti-Patterns (Banned AI Tells)
- No emojis.
- No rounded corners on cards or terminals (strictly 0px).
- No soft, blurred shadows (use solid block shadows or none).
- No generic icons (use custom SVG shapes or raw text symbols like `→`, `↳`, `■`).
- No centered layouts.
- No AI copywriting clichés ("Elevate", "Next-Gen", "Seamless").
- No fabricated statistics. If data is missing, use `[void]`.
