# Antigravity Premium Web-Dev Setup

Drop this into your project and restart Antigravity. Everything below is
built for React/Next.js sites that need to look and feel premium.

## 1. Install
Copy `AGENTS.md` and the `.agents/` folder into your **project root**
(same level as `package.json`). Commit both to git — this is meant to be
shared with the repo, not personal-only config.

```
your-project/
├── AGENTS.md
├── .agents/
│   ├── mcp_config.json
│   ├── rules/
│   │   ├── design-system.md
│   │   ├── coding-style.md
│   │   └── security.md
│   ├── agents/
│   │   ├── architect/agent.md
│   │   ├── ui-motion-designer/agent.md
│   │   ├── backend-engineer/agent.md
│   │   └── qa-verifier/agent.md
│   └── skills/
│       ├── website-builder/SKILL.md
│       ├── motion-design/SKILL.md
│       ├── security-review/SKILL.md
│       └── performance-audit/SKILL.md
└── package.json
```

If you want these available for **every** project (not just this one),
copy the `.agents/agents/*` and `.agents/skills/*` folders instead into
`~/.gemini/config/agents/` and `~/.gemini/config/skills/` respectively.

## 2. Restart Antigravity
Open `/agents` (or the Agent Manager panel) — you should see `architect`,
`ui-motion-designer`, `backend-engineer`, and `qa-verifier` listed as
available custom agents. Rules load automatically at the start of every session.

## 3. Fill in the MCP config
Edit `.agents/mcp_config.json` and swap in a real GitHub personal access
token (or delete the block if you don't want GitHub MCP yet). Never commit
a real token — use an env var reference if your Antigravity version supports
`${GITHUB_TOKEN}`-style interpolation, otherwise keep this file out of git
and load it from the global config path instead.

## 4. How to actually use it day to day

**Starting something new:**
> "@architect — I want to build [X]. Here's what it's for and who it's for."

Let it read the repo, propose a plan, and tell you which agent takes each phase.

**Building a section:**
> "@ui-motion-designer — build the hero with a 3D floating object and
> scroll-triggered reveal for the text."

**Backend work:**
> "@backend-engineer — wire up the contact form to send an email and store
> the submission."

**Before calling something done:**
> "@qa-verifier — check this page."

You can also just talk to the default/main agent normally — it knows (via
`AGENTS.md`) to hand work to the right specialist automatically.

## 5. Install the npm packages the motion skill expects
```bash
npm install framer-motion gsap lenis
# only if you're doing 3D:
npm install three @react-three/fiber @react-three/drei
```

## 6. First things to do in a fresh project
1. `git init && git add -A && git commit -m "init"` — before any agent touches it
2. Ask `@architect` to review the repo and propose the initial page/component structure
3. Set up design tokens (colors, type scale, spacing) before building real pages
