# Claude Code Plan Mode Guide

## What Is Plan Mode?

Plan mode (`--permission-mode plan`) is a **read-only operating mode** for Claude Code. In this mode, Claude will:

1. Explore your codebase (read files, search, analyze)
2. Reason through the task step by step
3. Write a detailed implementation plan to a plan file
4. **Stop and wait for your approval** before doing anything else

No files are written, no commands are run, no git commits are made — until you explicitly approve the plan.

---

## How to Use Plan Mode

```bash
claude --permission-mode plan "Your task description here"
```

**Example:**

```bash
claude --permission-mode plan "Add rate limiting to all public API endpoints"
```

Claude will explore the codebase, identify the relevant files and patterns, and produce a plan like:

```
## Plan: Add Rate Limiting to Public API Endpoints

### Context
The API currently has no rate limiting. This change adds per-IP rate limiting
using the existing `express-rate-limit` package (already a dependency).

### Files to Modify
- src/app.js — apply rate limiter middleware globally
- src/routes/public.js — add stricter limits on auth endpoints

### Steps
1. Configure a default rate limiter (100 req/15min per IP)
2. Configure a strict limiter for /login and /register (10 req/15min)
3. Apply default limiter in app.js before route registration
4. Apply strict limiter in public.js on auth routes

### Verification
- Run existing tests: npm test
- Manually test with curl to confirm 429 responses after limit exceeded
```

Once you review and approve the plan, Claude proceeds with execution.

---

## Why Use Plan Mode?

### 1. Understand before committing

For complex tasks spanning many files, plan mode lets you verify Claude's understanding matches your intent — before any code is touched.

### 2. Catch misunderstandings early

If Claude misunderstood the task, you'll see it in the plan and can correct it with a follow-up message rather than undoing changes.

### 3. Required review workflows

In team settings or regulated environments, plan mode provides a natural review checkpoint. The plan can be inspected, discussed, or logged before execution.

### 4. Explore unfamiliar codebases safely

When working on code you don't fully know yet, plan mode lets Claude map out what it would do without the risk of accidental changes.

---

## Writing Effective Task Descriptions for Plan Mode

The quality of the plan depends on the clarity of your description. Follow these guidelines:

### Be specific about scope

| Vague | Better |
|---|---|
| "Fix the auth" | "Fix the JWT token expiry check in `src/middleware/auth.js` — it's not rejecting expired tokens" |
| "Clean up the database code" | "Refactor `src/db/queries.js` to use parameterized queries throughout and remove the raw SQL string concatenation" |

### State constraints and requirements

```
Add a caching layer for the /products endpoint.
Requirements:
- Use Redis (already configured in src/cache.js)
- Cache TTL: 5 minutes
- Invalidate on any product update or delete
- Do not cache requests with authentication headers
```

### Mention what NOT to change

```
Migrate the user model from callbacks to async/await.
Do NOT change the API contract — keep all existing function signatures the same.
```

---

## Reviewing the Plan

When Claude presents a plan, check for:

- **Correct files identified** — Does it reference the right files? Are any important ones missing?
- **Accurate understanding** — Does the plan reflect what you actually want?
- **Reasonable steps** — Are the steps logical and in the right order?
- **Scope creep** — Is Claude proposing changes beyond what you asked for?
- **Risk assessment** — Does the plan note any risky or irreversible actions?

### Approving the plan

Once satisfied, approve the plan and Claude will execute it.

### Requesting changes

If the plan needs adjustments, describe what to change:

```
The plan looks good but step 3 is wrong — don't modify the global middleware,
only apply the rate limiter to the /api/v1/public/* routes.
```

---

## Plan Mode vs Default Mode

| Situation | Recommended Mode |
|---|---|
| Large refactor across many files | Plan mode |
| Unfamiliar codebase | Plan mode |
| Required human approval step | Plan mode |
| Small, well-understood change | Default mode |
| Quick bug fix | Default mode |
| Automated pipeline | `bypassPermissions` |

---

## Tips

- **Plan mode is free to run repeatedly.** If the first plan isn't right, refine your description and run again.
- **Use plan mode as documentation.** The generated plan is a useful record of what was done and why.
- **Combine with specific model selection** for complex plans: `claude --permission-mode plan --model claude-opus-4-6 "..."`.
- **Plan mode respects `.claude/` configuration** — your `CLAUDE.md`, settings, and tools are all active.
