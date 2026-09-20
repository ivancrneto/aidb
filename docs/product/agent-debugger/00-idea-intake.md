# Idea: Agent debugger (live attach)

**Logged by:** Ivan Neto · **Date:** 2026-09-20 · **Status:** New

## One-liner
Developers debugging multi-agent apps can attach to a live run. They can stop on a model reply or control transfer, edit that value, and resume the same run.

## Trigger
Internal pain first: the team lacks a pdb-style debugger while building multi-agent apps, and the market mostly offers post-run traces. Secondary bet: open-source the same runtime so others can plug it in, with IDE and CLI clients later.

## Problem
When developers change prompts or agent behavior, they need to stop a new run mid-flight. They need to inspect a bad model reply or a bad handoff, including a tool that owns the next chunk of work. They need to rewrite that value and continue the same run. Today they get finished traces, approval pauses, or record-replay of yesterday's tape. Those tools do not give live step, enter, and edit-and-resume on the current attempt. The pain shows up in local and lower environments that use mocked side effects.

## Who is affected
Primary: the team's developers who debug multi-agent apps in local and lower environments. Secondary: external developers who adopt the open-source runtime. IDE and CLI surfaces (VS Code, PyCharm, Cursor, Claude Code, and similar) are later clients over the same attach runtime. The first wedge is attach to the multi-agent app process.

## Why now
Multi-agent and non-deterministic agent work already consume developer time. Market research for this idea found no shipped pdb-equivalent for live attach outside LangGraph Studio's graph-node model.

## Rough size
XL. Reasoning: v1 needs a control-transfer runtime with edit-and-resume plus one thin client for the team. It also needs an open-source plug-in path, and a stated path to IDE and CLI clients even if those adapters ship later.

## Related context
- Brainstorm locked in session 2026-09-20 (attach to app process; control transfer = model reply, tool, agent handoff; edit-and-resume; traces and record-replay later).
- Landscape survey canvas: `.cursor/projects/Users-ivan-code-aidb/canvases/ai-agent-debugger-landscape.canvas.tsx`
- Closest analogs researched: LangGraph Studio, AGDebugger (CHI 2025), AgentStepper (2026).

## Decision needed
[ ] Promote to PRD   [ ] Park   [ ] Merge into existing workstream: ______
**Decided by / on:** ______
