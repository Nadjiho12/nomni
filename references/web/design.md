# Web design

*Last updated: 2026-09-30 | Version-sensitive: font licensing and availability; framework defaults | Re-check current docs before pinning versions, prices, or API names.*

Purpose: make interfaces look intentional, not templated. Pick a direction, then apply tokens, layout recipes, and component rules consistently. If a dedicated frontend-design skill is available, read it too.

## Contents
1. Aesthetic directions
2. Token starter sets
3. Typography
4. Layout recipes
5. Landing page anatomy
6. Dashboard and app UI
7. Components checklist
8. Motion
9. Design QA

## 1. Aesthetic directions (pick one, commit)

| Direction | Signals | Type | Palette |
|---|---|---|---|
| Minimal editorial | Big whitespace, thin rules, one accent | Serif display + clean sans | Off-white, near-black, one hue |
| Dark tech / cyber | Dark surfaces, mono accents, subtle glow | Grotesk + monospace | Charcoal, cyan/lime accent |
| Brutalist | Hard borders, raw grid, oversized type | Heavy grotesk or mono | Black, white, one loud color |
| Soft / friendly | Rounded shapes, pastel gradients | Rounded sans | Pastels with a strong text color |
| Retro / pixel | Chunky borders, limited palette, pixel font | Pixel or slab | 4-8 fixed colors |
| Glass / futuristic | Translucent layers, blur, gradients | Geometric sans | Deep blues/violets with light accents |
| Corporate clean | Structured grid, blue-grey, clear hierarchy | Neutral sans | Blues, greys, one warm accent |

State the chosen direction in one line before building; it prevents mixed styles.

## 2. Token starter sets

```css
/* Dark tech */
:root{--bg:#0b0e14;--surface:#121722;--line:#1f2937;--fg:#e6edf3;--muted:#8b98a9;--accent:#22d3ee;--ok:#34d399;--warn:#fbbf24;--bad:#f87171;
      --r:10px;--shadow:0 8px 30px #0008;--font:'Inter',system-ui,sans-serif;--mono:'JetBrains Mono',ui-monospace,monospace}
/* Editorial light */
:root{--bg:#faf8f4;--surface:#fff;--line:#e6e1d8;--fg:#1a1a1a;--muted:#6b665e;--accent:#b4381e;--r:2px;--font:'Source Serif 4',Georgia,serif}
```

Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64, 96. Radii: pick one or two. Shadows: at most two levels.

## 3. Typography

- Two families max (display + text), or one family with weight contrast.
- Scale (ratio 1.25): 12 / 14 / 16 / 20 / 25 / 31 / 39 / 49. Use `clamp()` for headings.
- Body 16-18px, line-height 1.5-1.7; headings 1.1-1.25; line length 55-75ch.
- Fallback stacks for every custom font; `font-display: swap`.

## 4. Layout recipes

- **Hero**: headline (6-10 words) + one sentence + one primary button + proof (logo row, number, screenshot).
- **Feature grid**: 3 or 6 cards, icon + title + one line; avoid walls of text.
- **Split section**: 50/50 text and visual, alternate sides.
- **Sticky sidebar docs**: nav left (240px), content 70ch, TOC right.
- **Bento grid**: CSS Grid with `grid-template-areas`, mixed-size tiles; keep 4-6 tiles.
- Rhythm: consistent vertical spacing between sections (96px desktop, 64px mobile).

## 5. Landing page anatomy

1. Header (logo, 3-5 links, one CTA)
2. Hero (value proposition + CTA + visual)
3. Social proof (logos, testimonial, metric)
4. Problem → solution (short)
5. Features/benefits (outcomes first)
6. How it works (3 steps)
7. Pricing or offer (if any)
8. FAQ (objections)
9. Final CTA
10. Footer (links, contact, legal)

One primary action repeated, everything else secondary. Write copy in the reader's words; remove any sentence that does not help a decision.

## 6. Dashboard and app UI

- Layout: left nav or top bar, content grid, consistent card component.
- Top row: 3-4 KPI tiles (value, delta, sparkline). Below: primary chart, then tables.
- Charts: line for trends, bar for comparison, stacked bar for composition, no 3D or pie with more than 5 slices.
- Tables: sticky header, right-align numbers, sortable columns, empty and loading states, row actions in a menu.
- Filters live above the data and show active state; provide a clear-all.
- Every view needs: loading skeleton, empty state with next action, error state with retry.

## 7. Components checklist

Buttons (primary/secondary/ghost/destructive, disabled, loading) · inputs (label, hint, error, disabled) · select/combobox · checkbox/radio/switch · tabs · modal/drawer (focus trap, Esc closes) · toast · tooltip · dropdown menu · pagination · badge · avatar · breadcrumb · progress. Define each once, reuse everywhere. Target size at least 44px on touch.

## 8. Motion

Purposeful only: 150-250 ms for UI feedback, 300-500 ms for page transitions, ease-out for entering, ease-in for leaving. Animate transform/opacity. Stagger lists by 30-60 ms. Respect `prefers-reduced-motion`.

## 9. Design QA

Contrast at least 4.5:1 for text · one primary action per view · consistent spacing and radii · keyboard focus visible · works at 360px · dark and light both tested if supported · no text over busy imagery without a scrim · icons from one set · real content, not lorem ipsum, in the final pass.
