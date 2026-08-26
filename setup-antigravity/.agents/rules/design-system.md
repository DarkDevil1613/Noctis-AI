# Design System Rules — "Premium" Standard

Every page built for this project must clear this bar before it's considered done.
The goal: it should feel like a studio-built product site, not an AI-generated template.

## Visual hierarchy
- One clear focal point per section. Never more than 2 competing accents on screen.
- Type scale: use a real scale (e.g. 14/16/18/24/32/48/64/96px), never arbitrary sizes.
- Generous whitespace over dense layouts. When in doubt, add more space, not more content.
- Dark-first by default unless the brief says otherwise; always support light mode via
  CSS variables, never hardcoded hex in components.

## Explicitly avoid ("AI slop" tells)
- Generic centered hero with gradient blob + giant heading + two pill buttons
- Overused glassmorphism / frosted panels everywhere
- Purple-to-blue gradients as a default accent (pick an intentional palette instead)
- Emoji as icons; use a real icon set (Lucide, Phosphor, or custom SVG)
- Stock-photo hero images
- Uniform 3-card "feature grid" as the only content pattern on the page

## Motion philosophy
- Motion should support meaning (reveal on scroll, connect cause → effect), not
  decorate randomly. If you can't explain why something animates, cut it.
- Respect `prefers-reduced-motion` — always provide a reduced/no-motion path.
- Nothing should feel laggy: target 60fps, no janky scroll, no layout shift
  from animations. See the `motion-design` skill for implementation rules.

## Responsive rules
Every page/component must be verified at:
- 375px (mobile)
- 768px (tablet)
- 1024px (small laptop)
- 1440px (desktop)
Mobile-first CSS. No horizontal scroll ever, unless it's an intentional carousel.

## Typography & color
- Max 2 font families (1 display + 1 body), loaded via `next/font` (no FOUT/FOUC).
- Color palette: 1 background, 1–2 accent colors, 1 semantic error/success pair.
  Define all as Tailwind theme tokens / CSS variables — never one-off hex codes
  scattered through components.

## Accessibility (non-optional, not just nice-to-have)
- Contrast ratio ≥ 4.5:1 for body text.
- All interactive elements keyboard-navigable and have visible focus states.
- Custom cursors and heavy motion must degrade gracefully on touch devices.
