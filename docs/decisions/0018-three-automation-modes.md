---
status: accepted
date: 2025-09-15
---
# ADR-0018: Three Automation Modes — Manual/Semi/Auto

## Context
Different operators have different comfort levels with agent autonomy. Some want full control over every action, others want the agent to handle routine work independently. A single automation level forces a one-size-fits-all tradeoff between safety and efficiency.

## Decision
The platform supports three automation modes: manual (agent proposes, human executes), semi-auto (agent executes routine operations, asks for non-routine), and auto (agent executes all operations within safety invariants). This is the core operational contract between human and agent.

## Alternatives Considered
- **Single automation level** — forces all operators into the same workflow; too restrictive or too permissive
- **Per-command granular permissions** — configuration explosion; difficult to reason about aggregate behavior

## Consequences
Operators choose their comfort level without forking the platform. The semi-auto mode handles the common case well. Mode boundaries must be clearly documented so operators understand what the agent will do autonomously in each mode.
