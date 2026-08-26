---
name: website-builder
description: End-to-end workflow for building a new site or major feature to a premium standard — plan, design, implement, test, verify. Use whenever starting a new project or a substantial new page/section.
---

# Website Builder Workflow

Run these phases in order. Don't skip to implementation.

## 1. Plan (architect agent)
Scope the project, audit the existing repo, produce a phased implementation
plan. Wait for approval on anything non-trivial.

## 2. Design system check (design-system.md rules)
Before building new pages, confirm: type scale, color tokens, spacing scale,
and breakpoints are defined. If this is a brand-new project, set these up
first — everything else builds on top.

## 3. Structure
Build static structure and layout first — no animation yet. Get the content,
hierarchy, and responsiveness right at all four breakpoints before adding motion.

## 4. Backend (backend-engineer agent, if needed)
Wire up any forms, data fetching, or dynamic content. Validate, handle errors,
test the actual request/response.

## 5. Motion pass (ui-motion-designer agent)
Now layer in animation: scroll reveals, micro-interactions, 3D if planned,
loading states, custom cursor, page transitions. One section at a time,
checking performance after each.

## 6. Verify (qa-verifier agent)
Full pass: console errors, all breakpoints, all interactive flows, scroll
behavior, loading states.

## 7. Security + performance pass
Run the `security-review` and `performance-audit` skills before calling
anything deploy-ready.

## 8. Git checkpoint
Commit with a clear message once a phase is verified. This is the rollback
point if the next phase goes wrong.

## Never
- Add motion before the static layout is responsive and correct
- Call something done without a `qa-verifier` pass
- Skip the plan phase for anything bigger than a one-file fix
