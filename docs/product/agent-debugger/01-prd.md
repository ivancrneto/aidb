# PRD: Agent debugger (live attach)

**Owner:** Ivan Neto · **Track:** 1 · **Status:** Draft
**Date:** 2026-09-20 · **Milestone target:** timing lives in the ship summary (05); section 9 defines the milestone outcome

## 1. Summary
This workstream delivers a live-attach debugger for multi-agent apps. A developer attaches to a running app in local or lower environments. They stop on a model reply or a handoff (tool or agent). They edit that value and resume the same run so the next step uses the edit. The first milestone includes one thin client for the team and an open-source plug-in path for external adopters. Full traces, record-replay of earlier runs, and IDE or CLI adapters are later layers on the same product family.

## 2. Problem & context
Developers iterating on multi-agent prompts and behavior cannot stop a live run at a bad model reply or a bad handoff. That includes when a tool owns the next chunk of work. They cannot rewrite that value and continue. They rely on finished traces, approval pauses, or replaying an earlier tape. None of those support live step, enter, and edit-and-resume on the current attempt in local and lower environments with mocked side effects. The team is already building multi-agent apps without this capability. This session's market survey found no shipped pdb-equivalent for live attach outside LangGraph Studio's graph-node model.
**Product fit:** This is the first product of the `aidb` repo: a live-attach debugger for multi-agent apps, with traces and IDE/CLI clients planned as later layers on the same runtime.

## 3. Users
Primary: the team's developers who debug multi-agent apps in local and lower environments. Secondary: external developers who adopt the open-source runtime once published. Buyers and approvers for this cycle are the same team; there is no separate external buyer. Future IDE and CLI clients serve these same users; they are not a separate persona for this PRD.

## 4. Goals
1. Developers can stop a live multi-agent run at a bad model reply or handoff, edit that value, and continue the same run with the edit applied.
2. The team can complete that workflow in local and lower environments using the first-milestone client surface.
3. External developers can plug the runtime into their own agents through the published open-source path.

## 5. Scope
**In scope:**
- Attach to a multi-agent app process for a new live run
- Stop after a model reply and inspect it before the next owner trusts it
- Stop on a handoff when control passes to a tool or another agent, and inspect the baton
- Edit the stopped value and resume the same run so the next step uses the edit
- Step to the next stop, enter into a tool or nested agent, and continue
- One thin client for the team enough to exercise the above
- Open-source plug-in path so an external developer can adopt the runtime
- Local and lower environments that use mocked side effects

**Out of scope / non-goals:**
- Full post-run trace and eval products as the primary debugger
- Record-replay or splicing a change into yesterday's completed run
- LangGraph-only or any single framework as a hard requirement for the core experience
- IDE adapters (VS Code, PyCharm, Cursor) and CLI agent clients (Claude Code and similar) in this milestone
- Production attach against real irreversible side effects (live email, live card charges)
- Automated attribution or repair of agent failures without a human at the stop

## 6. Key requirements
- **REQ-1:** A developer can attach the debugger to a running multi-agent app process in local or lower and halt the run at a controlled stop.
- **REQ-2:** A developer can stop after a model reply and inspect it. The next owner does not treat the original reply as final until the developer resumes.
- **REQ-3:** A developer can stop on a handoff when control passes to a tool or another agent, inspect the baton, and choose to continue.
- **REQ-4:** A developer can edit the stopped model reply or handoff baton and resume the same run so the next step consumes the edited value.
- **REQ-5:** A developer can step to the next model-reply or handoff stop. They can enter into a tool or nested agent as its own stop sequence. They can continue until the next stop or the end of the run.
- **REQ-6:** The team can complete REQ-1 through REQ-5 using one thin client shipped in this milestone.
- **REQ-7:** An external developer can plug the runtime into their own agent through the published open-source path and reach a controlled stop on a model reply or handoff.

## 7. Dependencies & risks
**Depends on:**
- A sample or team multi-agent app available in local or lower with mocked side effects for dogfood and the milestone demo
- Decision on which thin client ships first (TODO — owner: Ivan Neto)

**Risks:**
- Framework diversity may block a single attach story. Mitigate by defining handoff and model-reply stops as the shared contract. Treat framework adapters as implementer work outside this PRD's requirements list.
- Edit-and-resume may diverge from true environment state if a tool already ran. Mitigate by stopping before the next owner trusts the baton and by limiting the milestone to mocked side effects.
- Open-source publish may lag the team client. Mitigate by treating REQ-7 as required for the milestone.

## 8. Success metrics
1. TODO — owner: Ivan Neto (pairs with Goal 1)
2. TODO — owner: Ivan Neto (pairs with Goal 2)
3. TODO — owner: Ivan Neto (pairs with Goal 3)

## 9. Milestone
A teammate debugging a sample multi-agent app can attach to a live run, stop on a model reply or handoff, edit that value, and resume the same run. They can show that the next step used the edit. Shown or not shown.

## 10. Open questions
- Which thin client ships first for the team (local web UI vs another surface)? Owner: Ivan Neto
- What are the numeric or qualitative targets for section 8 after a dogfood week? Owner: Ivan Neto
- Which sample multi-agent app is the milestone demo vehicle? Owner: Ivan Neto
