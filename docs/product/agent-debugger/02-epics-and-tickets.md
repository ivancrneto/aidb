# Epics & Tickets: Agent debugger (live attach)

Derived from `01-prd.md`. Every ticket cites the PRD requirement it implements.
Titles become the GitHub Issue summaries verbatim at Stage 4.
Tracker: GitHub Issues on `ivancrneto/aidb` (not Jira).

## Initiative: Live attach: stop edit resume for multi-agent apps · new
**Purpose:** Developers iterating on multi-agent prompts and behavior cannot stop a live run at a bad model reply or handoff, rewrite that value, and continue. This initiative serves the team's developers in local and lower first, then external adopters through a published path.

## Epic A: Live attach: halt a live multi-agent run · new  *(implements REQ-1)*
**Purpose:** Developers need a live multi-agent run they can attach to and halt. This epic ships a mocked sample app and the ability to attach and stop a run already in progress.

| Ticket | Title | Type | Implements | Start before design? | Depends on | GitHub |
|--------|-------|------|-----------|----------------------|------------|--------|
| TKT-A1 | Live attach: mocked sample multi-agent app | dev | REQ-1 | Yes | (none) | |
| TKT-A2 | Live attach: attach and halt a live run | dev | REQ-1 | Yes | TKT-A1 | |

**TKT-A1: Live attach: mocked sample multi-agent app**
As a developer, I can run an in-repo sample multi-agent app in local or lower with mocked side effects. The app produces model replies and handoffs so the milestone demo has a vehicle to attach to. No debugger UI in this ticket.

**TKT-A2: Live attach: attach and halt a live run**
As a developer, I can attach to a live multi-agent run from the sample app in local or lower and halt it at a controlled stop. The run stays halted until I continue or end the session.

## Epic B: Stop points: hold on reply and handoff · new  *(implements REQ-2, REQ-3)*
**Purpose:** Developers need to stop when a model reply or a handoff is about to drive the next step. This epic makes those stops inspectable before the run continues.

| Ticket | Title | Type | Implements | Start before design? | Depends on | GitHub |
|--------|-------|------|-----------|----------------------|------------|--------|
| TKT-B1 | Stop points: hold after model reply | dev | REQ-2 | Yes | TKT-A2 | |
| TKT-B2 | Stop points: hold on tool or agent handoff | dev | REQ-3 | Yes | TKT-A2 | |

**TKT-B1: Stop points: hold after model reply**
As a developer, I can stop after a model reply and inspect it. The run does not continue on that reply until I resume.

**TKT-B2: Stop points: hold on tool or agent handoff**
As a developer, I can stop when control passes to a tool or another agent, inspect the handoff value, and choose to continue.

## Epic C: Edit resume: next step uses edited value · new  *(implements REQ-4)*
**Purpose:** Developers who find a bad reply or handoff at a stop need to rewrite it and continue the same run. This epic serves those developers so the next step consumes the edit.

| Ticket | Title | Type | Implements | Start before design? | Depends on | GitHub |
|--------|-------|------|-----------|----------------------|------------|--------|
| TKT-C1 | Edit resume: edit reply or handoff and continue | dev | REQ-4 | Yes | TKT-B1, TKT-B2 | |

**TKT-C1: Edit resume: edit reply or handoff and continue**
As a developer, I can edit the stopped model reply or handoff value and resume the same run. The next step consumes the edited value. I can show that the next step used the edit.

## Epic D: Step enter: advance into nested work · new  *(implements REQ-5)*
**Purpose:** Developers need to move across stops the way they step through ordinary code. This epic delivers step to the next stop, enter into a tool or nested agent, and continue.

| Ticket | Title | Type | Implements | Start before design? | Depends on | GitHub |
|--------|-------|------|-----------|----------------------|------------|--------|
| TKT-D1 | Step enter: step, enter, and continue | dev | REQ-5 | Yes | TKT-B1, TKT-B2 | |

**TKT-D1: Step enter: step, enter, and continue**
As a developer, I can step to the next model-reply or handoff stop. I can enter a tool or nested agent and stop inside it. I can continue until the next stop or the end of the run.

## Epic E: Team UI: complete workflow in local web · new  *(implements REQ-6)*
**Purpose:** The team needs one shipped surface to complete attach, stop, edit, resume, step, and enter. This epic delivers that local web workflow for developers in local and lower.

| Ticket | Title | Type | Implements | Start before design? | Depends on | GitHub |
|--------|-------|------|-----------|----------------------|------------|--------|
| TKT-E1 | Team UI: provisional local web for full stop workflow | dev | REQ-6 | Yes | TKT-A2, TKT-C1, TKT-D1 | |
| TKT-E2 | Team UI: local web workflow screens | design | REQ-6 | (n/a) | (none) | |
| TKT-E3 | Team UI: complete milestone path in local web | dev | REQ-6 | No | TKT-E1, TKT-E2, TKT-D1 | |

**TKT-E1: Team UI: provisional local web for full stop workflow**
As a developer, I can drive attach, halt, reply hold, handoff hold, edit-and-resume, step, and enter from a provisional local web surface. Layout and visual design are not final in this ticket.

**TKT-E2: Team UI: local web workflow screens**
Design delivers every screen and flow for the local web surface. That includes attach to a live run, halted-run views of model reply and handoff value, edit-and-resume, step, enter, and continue.

**TKT-E3: Team UI: complete milestone path in local web**
As a developer, I can complete the milestone path in the designed local web surface. I attach, stop on reply or handoff, edit, resume with the edit applied, and perform one step or enter on the sample app in local or lower.

## Epic F: Publish path: external developer controlled stop · new  *(implements REQ-7)*
**Purpose:** External developers need a published path to get a controlled stop on their own agent. This epic makes that path followable without the team's private apps.

| Ticket | Title | Type | Implements | Start before design? | Depends on | GitHub |
|--------|-------|------|-----------|----------------------|------------|--------|
| TKT-F1 | Publish path: documented plug-in steps | dev | REQ-7 | Yes | (none) | |
| TKT-F2 | Publish path: external agent reaches controlled stop | dev | REQ-7 | No | TKT-F1, TKT-B1, TKT-B2 | |

**TKT-F1: Publish path: documented plug-in steps**
As an external developer, I can follow published plug-in steps that cover prerequisites, how to attach my agent, how to reach a controlled stop on a model reply or handoff, and how to confirm success. Deliverable is the doc set and any diagrams the path needs.

**TKT-F2: Publish path: external agent reaches controlled stop**
As an external developer following the published path on my own agent, I can reach a controlled stop on a model reply or handoff. I do not need the team's private apps.

## Requirements not yet ticketable
(none)

## Decisions recorded this stage
- Tracker: GitHub Issues on `ivancrneto/aidb`
- Initiative: new tracking issue, area tag Live attach
- First shipped surface: local web UI
- Sample app: in-repo sample with mocked side effects
