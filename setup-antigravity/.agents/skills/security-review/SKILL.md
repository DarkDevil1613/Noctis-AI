---
name: security-review
description: Run a full security pass over the project before a deploy-worthy milestone. Checks secrets, input validation, auth, and common web vulnerabilities.
---

# Security Review Skill

Check for, and report/fix as appropriate:

- Hardcoded secrets, API keys, or tokens anywhere in the codebase
  (`grep` for common patterns: `sk-`, `api_key`, `password =`, etc.)
- `.env` committed to git, or missing from `.gitignore`
- Unvalidated user input reaching the database or filesystem
- SQL/NoSQL injection risk (raw string queries instead of parameterized/ORM)
- XSS risk: unescaped user content rendered with `dangerouslySetInnerHTML`
- CSRF exposure on state-changing routes without protection
- Auth checks missing on server routes/actions that should require login
- Overly permissive CORS (`*` on routes handling user data)
- File upload endpoints without type/size validation
- Sensitive data (tokens, PII) appearing in client-side bundles or logs
- Outdated dependencies with known vulnerabilities (`npm audit`)
- Debug endpoints or verbose error messages exposed in production

## Output
A prioritized list: Critical (fix before deploy) / Moderate (fix soon) /
Low (note for later). Fix Critical items directly; report the rest.
