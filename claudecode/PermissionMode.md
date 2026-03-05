# Claude Code Permission Mode Guide

## Overview

Claude Code supports multiple **permission modes** that control how autonomously it operates and which actions it will take without asking for your confirmation. Choosing the right mode helps you balance speed, safety, and oversight.

---

## Permission Modes

### `default` (Standard Mode)

Claude Code operates interactively, asking for confirmation before taking potentially risky or irreversible actions such as:

- Writing or deleting files
- Running shell commands
- Making network requests
- Pushing to git remotes

**Best for:** Day-to-day development where you want to stay in control of what happens on your system.

```bash
claude                        # default mode
claude --permission-mode default
```

---

### `plan` (Plan-Only Mode)

Claude Code enters a **read-only** state. It will explore your codebase, reason about the task, and produce a detailed implementation plan — but it will **never execute** any changes. You review the plan and explicitly approve it before any code is written or commands are run.

**Best for:**
- Reviewing a complex change before committing to it
- Understanding what Claude intends to do before letting it act
- Teams or contexts where human review is required before execution
- Onboarding to a new codebase without risk

```bash
claude --permission-mode plan
```

---

### `bypassPermissions` (Autonomous Mode)

Claude Code operates fully autonomously, bypassing all confirmation prompts. It will read files, write files, run shell commands, and take other actions without pausing for approval.

> **Warning:** Only use this mode in trusted, sandboxed, or automated environments (e.g., CI pipelines, Docker containers). Never use it on a production system or a machine with sensitive data unless you fully trust the task and have backups.

**Best for:**
- Automated pipelines and CI/CD workflows
- Sandboxed test environments
- Batch scripting with well-defined, low-risk tasks

```bash
claude --permission-mode bypassPermissions
```

---

## Comparison Table

| Mode | Asks for confirmation | Can write/run | Use case |
|---|---|---|---|
| `default` | Yes (for risky actions) | Yes, after approval | Interactive development |
| `plan` | N/A (read-only) | No | Review before acting |
| `bypassPermissions` | No | Yes, immediately | Automated/trusted pipelines |

---

## Practical Examples

### Safely exploring a large refactor

```bash
# See what Claude would change before it touches anything
claude --permission-mode plan "Refactor all API handlers to use async/await"
```

### Running a trusted automation task

```bash
# In a sandboxed CI environment
claude --permission-mode bypassPermissions "Run tests, fix any failing ones, and commit"
```

### Normal interactive session (default)

```bash
# Claude will ask before writing files or running commands
claude "Add input validation to the user registration endpoint"
```

---

## Tips

- **Start with `plan` mode** when tackling an unfamiliar codebase or a large task — reviewing the plan first prevents surprises.
- **Use `bypassPermissions` only in isolated environments.** Treat it like `sudo`: powerful but requiring care.
- **`default` mode is the right choice for most work.** It keeps you informed while still letting Claude be productive.
- You can combine permission mode with other flags: `claude --permission-mode plan --model claude-opus-4-6 "..."`.
