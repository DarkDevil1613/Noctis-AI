---
name: performance-audit
description: Checks Core Web Vitals, bundle size, and runtime smoothness before calling a page done. Used by ui-motion-designer and backend-engineer.
---

# Performance Audit Skill

## Targets
- Lighthouse Performance score ≥ 90 on the built (production) site
- LCP < 2.5s, CLS < 0.1, INP < 200ms
- No single JS chunk over ~150kb gzipped without a lazy-load boundary
- 60fps during scroll and animation (check via devtools Performance tab)

## Checks, every pass
1. `next build` and check the route size output — flag any route that
   ballooned unexpectedly.
2. Images: served via `next/image`, correctly sized, modern format (webp/avif).
3. Fonts: loaded via `next/font`, no layout shift on font load.
4. Heavy libraries (Three.js, GSAP, large icon sets) are dynamically
   imported (`next/dynamic`) and not in the initial bundle unless needed
   above the fold.
5. No unused dependencies still imported "just in case."
6. Third-party scripts (analytics, embeds) loaded with `next/script`
   `strategy="lazyOnload"` or `afterInteractive`, not blocking render.
7. Run the page with CPU throttled 4x in devtools — confirm scroll and
   interactions stay smooth.

## Output
Report any target missed, with the specific cause (e.g. "LCP is 3.8s because
the hero image isn't using next/image") — not just the failing number.
