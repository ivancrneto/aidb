# Idea: Agent debugger (live attach)

**Logged by:** Ivan Neto · **Date:** 2026-09-20 · **Status:** Promoted

## One-liner
Developers debugging multi-agent apps can attach to a live run, stop on a model reply or a handoff (tool or agent), edit that value, and resume the same run.

## Trigger
Internal pain first: the team lacks a pdb-style debugger while building multi-agent apps, and the market mostly offers post-run traces. Secondary bet: open-source the same runtime so others can plug it in.

## Problem
Developers iterating on multi-agent prompts and behavior cannot stop a live run at a bad model reply or a bad handoff. That includes when a tool owns the next chunk of work. They cannot rewrite that value and continue. They rely on finished traces, approval pauses, or replaying an earlier tape. None of those support live step, enter, and edit-and-resume on the current attempt in local and lower environments with mocked side effects.

## Who is affected
Primary: the team's developers who debug multi-agent apps in local and lower environments. Secondary: external developers who adopt the open-source runtime once published. Future IDE and CLI clients (VS Code, PyCharm, Cursor, Claude Code, and similar) serve those same users; they are not a separate persona for intake.

## Why now
The team is already building multi-agent apps and burning time without a live debugger. This session's market survey found no shipped pdb-equivalent for live attach outside LangGraph Studio's graph-node model.

## Rough size
L for the first milestone (attach runtime, edit-and-resume, one thin client for the team, open-source plug-in path). XL if the workstream includes IDE and CLI adapters in the same initiative.

## Related context
- Brainstorm locked in session 2026-09-20 (attach to app process; control transfer = model reply, tool, agent handoff; edit-and-resume; traces and record-replay later).
- Landscape survey canvas: `.cursor/projects/Users-ivan-code-aidb/canvases/ai-agent-debugger-landscape.canvas.tsx`
- Closest analogs researched: LangGraph Studio, AGDebugger (CHI 2025), AgentStepper (2026).

## Decision needed
[x] Promote to PRD   [ ] Park   [ ] Merge into existing workstream: ______
**Decided by / on:** Ivan Neto / 2026-09-20
