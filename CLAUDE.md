# Claude operating policy

This repository is a constrained lab project. The agent must stay within the accepted specification and the locked decisions.

## Allowed work
- read and update project files in scope for Lab 1
- implement code and tests consistent with the approved decisions
- verify with `pytest` and `itsmlab.ps1 verify 1`

## Denylist
- no secrets, credentials, or private tokens in code or logs
- no destructive changes to the repo history or working tree outside the task
- no unrelated package or OS-level changes
- no alteration of the accepted design decisions or receipt-based specs

## Scope guard
If a request conflicts with the accepted spec, the agent must prefer the spec and explain the precedence briefly.
