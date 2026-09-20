# PRD: Agent debugger (live attach)

**Owner:** Ivan Neto · **Track:** 1 · **Status:** Approved
**Date:** 2026-09-20 · **Milestone target:** timing lives in the ship summary (05); section 9 defines the milestone outcome

## 1. Summary
This workstream delivers a live-attach debugger for multi-agent apps. A developer attaches to a running app in local or lower environments. They stop on a model reply or a handoff (tool or agent). They edit that value and resume the same run so the next step uses the edit. The first milestone includes one shipped surface for the team and an open-source plug-in path for external adopters. Full traces, record-replay of earlier runs, and IDE or CLI adapters are later layers on the same product family.

## 2. Problem & context
Developers iterating on multi-agent prompts and behavior cannot stop a live run at a bad model reply or a bad handoff. That includes when a tool owns the next chunk of work. They cannot rewrite that value and continue. They rely on finished traces, approval pauses, or replaying an earlier tape. None of those support live step, enter, and edit-and-resume on the current attempt in local and lower environments with mocked side effects. The team is already building multi-agent apps without this capability. This session's market survey found no shipped pdb-equivalent for live attach outside LangGraph Studio's graph-node model.
**Product fit:** Live attach is the foundation of `aidb`. Traces and IDE/CLI clients can share the same stop-and-edit model once this milestone lands.

## 3. Users
Primary: the team's developers who debug multi-agent apps in local and lower environments. Secondary success is covered by Goal 3 and REQ-7 (external plug-in path). Future IDE and CLI clients serve these same users.

## 4. Goals
1. Developers can stop a live multi-agent run at a bad model reply or handoff, edit that value, and continue the same run with the edit applied.
2. The team can complete that workflow in local and lower environments in this milestone.
3. External developers can follow the published open-source path on their own agents and reach controlled stops.

## 5. Scope
**In scope:**
- Attach to a live multi-agent run that is already in progress
- Stop after a model reply, inspect it, and keep the run from continuing on that reply until the developer resumes
- Stop on a handoff when control passes to a tool or another agent, and inspect the handoff value
- Edit the stopped value and resume the same run so the next step uses the edit
- Step to the next stop, enter into a tool or nested agent, and continue
- One shipped surface for the team enough to complete the in-scope workflow
- Published open-source path so an external developer can get a controlled stop on a model reply or handoff in their own agent
- Prove the workflow in local and lower environments where side effects are mocked

**Out of scope / non-goals:**
- Building a post-run trace or eval product in this milestone
- Record-replay or splicing a change into yesterday's completed run
- Requiring a specific agent framework for the sample app or for the milestone demo
- IDE adapters (VS Code, PyCharm, Cursor) and CLI agent clients (Claude Code and similar) in this milestone
- Attaching in production against real irreversible side effects in this milestone (for example live email or live card charges)
- Automated attribution or repair of agent failures without a human at the stop

## 6. Key requirements
- **REQ-1:** A developer can attach to a live multi-agent run in local or lower and halt it at a controlled stop.
- **REQ-2:** A developer can stop after a model reply and inspect it. The run does not continue on that reply until the developer resumes.
- **REQ-3:** A developer can stop on a handoff when control passes to a tool or another agent, inspect the handoff value, and choose to continue.
- **REQ-4:** A developer can edit the stopped model reply or handoff value and resume the same run so the next step consumes the edited value.
- **REQ-5:** A developer can step to the next model-reply or handoff stop. They can enter a tool or nested agent and stop inside it. They can continue until the next stop or the end of the run.
- **REQ-6:** The team can complete REQ-1 through REQ-5 using one shipped surface in this milestone.
- **REQ-7:** An external developer can follow the published open-source path on their own agent and reach a controlled stop on a model reply or handoff.

## 7. Dependencies & risks
**Depends on:**
- A sample or team multi-agent app available in local or lower with mocked side effects for dogfood and the milestone demo
- Decision on which shipped surface comes first (TODO — owner: Ivan Neto)

**Risks:**
- Framework diversity may block a single attach story. Mitigate by defining handoff and model-reply stops as the shared contract. Treat framework adapters as implementer work outside this PRD's requirements list.
- Edit-and-resume may diverge from true environment state if a tool already ran. Mitigate by stopping before the run continues on the stopped value and by limiting the milestone to mocked side effects.
- Open-source publish may lag the team surface. Mitigate by treating REQ-7 as required for the milestone.

## 8. Success metrics
1. TODO — owner: Ivan Neto (pairs with Goal 1)
2. TODO — owner: Ivan Neto (pairs with Goal 2)
3. TODO — owner: Ivan Neto (pairs with Goal 3)

## 9. Milestone
A teammate debugging a sample multi-agent app can attach to a live run, stop on a model reply or handoff, edit that value, and resume the same run. They can show that the next step used the edit. In the same demo they complete one step or enter action, and they follow a documented plug-in path on that sample app. Shown or not shown.

## 10. Open questions
- Which shipped surface comes first for the team (local web UI vs another surface)? **Resolved 2026-09-20:** local web UI. Owner: Ivan Neto
- What are the numeric or qualitative targets for section 8 after a dogfood week? Owner: Ivan Neto
- Which sample multi-agent app is the milestone demo vehicle? **Resolved 2026-09-20:** in-repo sample app with mocked side effects. Owner: Ivan Neto
