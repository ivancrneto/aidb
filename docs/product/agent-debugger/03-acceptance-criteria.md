# Acceptance Criteria: Agent debugger (live attach)

Derived from `02-epics-and-tickets.md`.
Stage 4 push target: GitHub Issues on `ivancrneto/aidb`.

## Epic A: Live attach: halt a live multi-agent run
- **AC-EA** (shippable): A developer can run the in-repo sample app with mocked side effects. They can attach to that live run in local or lower and halt it at a controlled stop until they continue or end the session.

### TKT-A1: Live attach: mocked sample multi-agent app
- **AC-A1.1** (happy): A developer can start the in-repo sample multi-agent app in local or lower. They observe at least one model reply and at least one handoff with mocked side effects.
- **AC-A1.2** (edge/negative): Starting the sample app does not open or require a debugger UI.

### TKT-A2: Live attach: attach and halt a live run
- **AC-A2.1** (happy): A developer can attach to a live sample-app run in local or lower and halt it at a controlled stop.
- **AC-A2.2** (edge/negative): While halted, the run does not advance to the next model reply or handoff until the developer continues or ends the session.

## Epic B: Stop points: hold on reply and handoff
- **AC-EB** (shippable): A developer can stop after a model reply and on a tool or agent handoff. They can inspect the stopped value. The run does not continue on that value until they resume.

### TKT-B1: Stop points: hold after model reply
- **AC-B1.1** (happy): A developer can stop after a model reply and inspect that reply. The run does not continue on it until they resume.
- **AC-B1.2** (edge/negative): If the developer resumes without editing, the run continues using the original reply.

### TKT-B2: Stop points: hold on tool or agent handoff
- **AC-B2.1** (happy): A developer can stop when control passes to a tool or another agent, inspect the handoff value, and choose to continue.
- **AC-B2.2** (edge/negative): While held at a handoff, the tool or nested agent does not proceed until the developer continues.

## Epic C: Edit resume: next step uses edited value
- **AC-EC** (shippable): A developer can edit a stopped model reply or handoff value and resume the same run. The next step uses the edited value.

### TKT-C1: Edit resume: edit reply or handoff and continue
- **AC-C1.1** (happy): A developer edits a stopped model reply, resumes, and the next step consumes the edited reply.
- **AC-C1.2** (happy): A developer edits a stopped handoff value, resumes, and the next step consumes the edited handoff value.
- **AC-C1.3** (edge/negative): Leaving the value unchanged and resuming continues with the original value.

## Epic D: Step enter: advance into nested work
- **AC-ED** (shippable): A developer can step to the next stop. They can enter a tool or nested agent and stop inside it. They can continue until the next stop or the end of the run.

### TKT-D1: Step enter: step, enter, and continue
- **AC-D1.1** (happy): From a stop, a developer can step to the next model-reply or handoff stop without ending the run.
- **AC-D1.2** (happy): From a handoff stop, a developer can enter the tool or nested agent and reach a stop inside it.
- **AC-D1.3** (happy): From a stop, a developer can continue until the next stop or the run ends.
- **AC-D1.4** (edge/negative): Continue on the last stop ends the run without error when there is no further stop.

## Epic E: Team UI: complete workflow in local web
- **AC-EE** (shippable): A developer can complete the milestone path in the local web surface on the sample app. That path is attach, stop on reply or handoff, edit, resume with the edit applied, and one step or enter.

### TKT-E1: Team UI: provisional local web for full stop workflow
- **AC-E1.1** (happy): From a provisional local web surface, a developer can attach, halt, hold on reply, hold on handoff, edit-and-resume, step, and enter.
- **AC-E1.2** (edge/negative): The provisional surface works without the final visual design from TKT-E2.

### TKT-E2: Team UI: local web workflow screens
- **AC-E2.1**: Design enables a developer to attach to a live run, inspect halted reply and handoff values, edit and resume, step, enter, and continue in local web. No milestone flow is missing.

### TKT-E3: Team UI: complete milestone path in local web
- **AC-E3.1** (happy, design-independent): A developer can complete attach, stop, edit, resume with edit applied, and one step or enter on the sample app in local or lower.
- **AC-E3.2** (pending design): The designed local web screens from TKT-E2 present that full milestone path without requiring a workaround flow.

## Epic F: Publish path: external developer controlled stop
- **AC-EF** (shippable): An external developer following the published path on their own agent reaches a controlled stop on a model reply or handoff. They do not need the team's private apps.

### TKT-F1: Publish path: documented plug-in steps
- **AC-F1.1** (happy): Published steps cover prerequisites, how to attach an external agent, how to reach a controlled stop on a model reply or handoff, and how to confirm success.
- **AC-F1.2** (edge/negative): A reader can confirm success or failure from the published steps without asking the team for private app access.

### TKT-F2: Publish path: external agent reaches controlled stop
- **AC-F2.1** (happy): An external developer following the published path reaches a controlled stop on a model reply or handoff on their own agent.
- **AC-F2.2** (edge/negative): Completing that path does not require the team's private apps or the sample app as a hard dependency for the external agent.
