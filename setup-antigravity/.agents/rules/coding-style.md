# Coding Style Rules

## Prefer
- Functional components, hooks, server components by default (App Router)
- `"use client"` only on components that actually need interactivity/state
- TypeScript everywhere — no `any` unless justified with a comment
- Small, composable components over large monolithic ones
- Named exports for components, colocated types
- Zod (or similar) for any data validation at boundaries (forms, API input)
- Descriptive names over comments; comment only non-obvious "why", not "what"

## Avoid
- Premature abstraction — don't build a generic system for one use case
- Prop drilling more than 2 levels — use context or composition instead
- Duplicated logic — extract a hook/util once it appears twice
- Magic numbers — name constants, especially for animation timing/breakpoints
- Adding a new dependency when the stack already has a tool that does it
- Giant files — split a component once it passes ~200 lines

## File structure convention
```
app/                 → routes (App Router)
components/ui/        → primitive, reusable UI (button, card, etc.)
components/sections/  → page-section-level components
components/motion/    → animation wrapper components (see ui-motion-designer)
lib/                  → utils, API clients, validation schemas
server/               → server-only logic (db, auth, actions)
```

## Before finishing any task
Run, in order: `npm run lint`, `npm run build`. Fix everything before
reporting back. If a test suite exists, run it too.
