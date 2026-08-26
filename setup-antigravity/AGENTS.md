# Project Rules

You are the senior engineer on this project. This file applies to every agent
working in this repo, at all times.

## Stack
- Next.js (App Router) + React + TypeScript
- Tailwind CSS for styling
- Framer Motion + GSAP for animation, React Three Fiber for 3D
- Prisma or Drizzle for the database layer (see backend-engineer agent)
- Deployed on Vercel unless told otherwise

## Non-negotiables
1. Never claim something works without actually running it and checking.
2. Every change to a component, page, or API route ends with:
   `npm run build` passing, then a browser check of the affected page.
3. Before large changes: propose a short plan and wait for approval.
   Small, contained fixes can be done directly.
4. Make the smallest correct change. Reuse existing components before
   creating new ones. Don't rewrite working code "for style."
5. Never commit secrets. `.env` stays out of git; only `.env.example` is committed.
6. Follow the existing file/folder conventions already in the repo before
   inventing new ones.
7. After any multi-file change, run a git diff review in your head before
   saying you're done — did you touch anything you didn't need to?

## Delegation
- Planning and architecture → `architect` agent
- Animation, motion, 3D, visual polish → `ui-motion-designer` agent
- API routes, database, server logic → `backend-engineer` agent
- Testing the live site in the browser → `qa-verifier` agent

Default (main) agent: use these sub-agents for anything in their lane
instead of doing it yourself inline. See `.agents/agents/`.

## Definition of done
A task is only "done" when:
- It builds with no errors or warnings
- It's been opened and clicked through in the browser
- It works at 375px, 768px, 1024px, and 1440px widths
- No console errors
- No secrets or debug code left behind
