---
name: motion-design
description: Concrete guidance for implementing scroll animations, 3D, loading screens, custom cursors, and smooth transitions without hurting performance. Used by the ui-motion-designer agent.
---

# Motion Design Skill

## Library decision table

| Effect you want | Use this |
|---|---|
| Fade/slide in on scroll | Framer Motion `whileInView` |
| Complex pinned/scrubbed scroll sequence | GSAP + ScrollTrigger |
| Buttery smooth page scroll | Lenis |
| 3D hero object / product viewer | React Three Fiber + drei, lazy-loaded |
| Small character/icon animation | Lottie (dotlottie-react) |
| Page-to-page transition | Framer Motion `AnimatePresence` or View Transitions API |
| Custom cursor | Framer Motion `motion.div` following pointer via transform |
| Number counters, progress bars | Framer Motion `useSpring`/`useMotionValue` |

Don't reach for GSAP for a simple fade-in — that's Framer Motion's job.
Don't reach for Three.js unless the brief actually calls for a 3D object;
a well-done CSS/SVG animation is often just as premium and far lighter.

## Setup checklist for a new project
1. Install: `framer-motion`, `gsap`, `lenis`, and (only if 3D is needed)
   `three`, `@react-three/fiber`, `@react-three/drei`.
2. Wrap the app in a Lenis smooth-scroll provider.
3. Create `components/motion/` with reusable wrappers: `<FadeIn>`,
   `<StaggerReveal>`, `<ParallaxLayer>` — build these once, reuse everywhere,
   rather than writing bespoke motion code in every section.
4. Add a global `prefers-reduced-motion` check; motion wrappers should read
   this and skip/simplify animation automatically.

## Loading animations
- Route-level: a branded splash/loader only for genuinely heavy first loads
  (large 3D scene, video-heavy hero). Don't add an artificial loader to a
  fast, light page just to seem premium — that's slower, not better.
- Component-level: skeleton screens for anything fetching data, blur-up
  (`next/image` `placeholder="blur"`) for images.

## Performance guardrails (check after every animation added)
- Animate `transform` and `opacity` only, wherever possible.
- Cap `devicePixelRatio` at 2 for any canvas/WebGL work.
- Pause/unmount heavy scenes when scrolled off-screen (`IntersectionObserver`).
- Use `will-change` sparingly — only on the element actively animating, and
  remove it after the animation completes.
- Debounce resize handlers; never run layout-affecting logic on every
  `scroll` event tick — use rAF or IntersectionObserver instead.
- Test on a throttled CPU (4x slowdown in devtools) — smooth there means
  smooth everywhere.

## Cursor implementation notes
- Use `translate3d`/`transform`, never `top`/`left`, to move the cursor —
  avoids layout recalculation on every mouse move.
- Disable entirely inside `@media (hover: none)` (touch devices).
- Provide a visible fallback default cursor for interactive elements when
  reduced motion is on.
