# Security Baseline (applies to every agent)

- Never hardcode API keys, tokens, or credentials in source. Use environment
  variables, referenced via `.env.example` with empty values.
- Validate and sanitize all user input on the server, even if it's validated
  on the client too.
- Any database query built from user input must use parameterized queries /
  the ORM's query builder — never raw string concatenation.
- Any file upload must validate type, size, and be stored outside of
  directly-executable paths.
- Auth checks belong on the server (route handlers / server actions),
  never trusted from the client alone.
- Set sane CORS rules — don't default to `*` on anything that touches
  user data.
- No secrets, tokens, or internal URLs in client-side bundles — check what
  actually ships to the browser, not just what's in the source file.
- Flag (don't silently "fix") anything touching auth, payments, or
  migrations — surface it for human review before proceeding.

Run the full `security-review` skill before any deploy-worthy milestone.
