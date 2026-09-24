# aidb

> Stop a live multi-agent run, rewrite a model reply or a handoff, and resume the same run so the next step uses the edit.

Live-attach debugger for multi-agent apps. Attach to a run that is already in progress, stop on a model reply or a handoff (tool or agent), edit that value, and continue. The next step consumes the edit.

## Why

- **The current attempt.** Attach to a run that is already going. Resume continues that same run.
- **Two stops.** Hold after a model reply, or on a handoff before a tool or nested agent runs.
- **An edit the next step reads.** Change the stopped reply or handoff value. Continue applies it.
- **A gate in your runtime.** The app calls `DebugSession` around each reply and handoff. The CLI attaches over a localhost JSON-line port.
- **Localhost and a token.** The control plane binds `127.0.0.1` only and requires a shared token on every command.

## How it works

```text
live run ──▶ gate ──▶ stop ──▶ edit ──▶ resume
 reply or     hold     inspect   rewrite   next step
 handoff      if armed value     value     uses the edit
```

Before the next reply or handoff, the runtime calls `gate_before_advance`. After the event is emitted, `gate_after_event` holds when that break is armed and returns the payload the next step should consume.

The control server speaks one JSON object per line over TCP. Every command returns JSON.

## Install

```bash
git clone https://github.com/ivancrneto/aidb.git
cd aidb
python -m pip install -e ".[dev]"
```

Requires Python 3.11+.

## Quick start

`samples/refund_desk` is a mocked multi-agent refund desk: an intake agent, a policy agent, and an in-memory `issue_refund` tool. It is a CLI process. With `--debug-port` it also prints a control port and token on stderr.

```bash
# 1. Start a paced run. stderr prints the port and token.
python -m samples.refund_desk --debug-port 8765 --pace 2

# 2. In another terminal, use the printed token.
export AIDB_CONTROL_TOKEN=...

# 3. Stop after each model reply.
python -m aidb break-reply --port 8765

# 4. Rewrite the held reply.
python -m aidb edit --port 8765 --content "Revised intake reply"

# 5. Resume. The next step uses the edit.
python -m aidb continue --port 8765
```

`--token` is optional when `AIDB_CONTROL_TOKEN` is set.

One interactive session:

```bash
python -m aidb attach --port 8765
```

Sample flags and the halt / handoff walkthrough are in [samples/refund_desk/README.md](samples/refund_desk/README.md).

## Commands

Every command takes `--port` (required), `--token` (or `AIDB_CONTROL_TOKEN`), and `--host` (default `127.0.0.1`).

### Attach

```bash
python -m aidb attach --port 8765
# halt | break-reply | clear-break-reply | break-handoff | clear-break-handoff
# edit content=... | edit value={...} | edit payload={...}
# continue (cont/c) | end | status | inspect | quit
```

### Breaks

```bash
python -m aidb break-reply --port 8765          # hold after each model reply
python -m aidb clear-break-reply --port 8765
python -m aidb break-handoff --port 8765        # hold each tool or agent handoff
python -m aidb clear-break-handoff --port 8765
python -m aidb halt --port 8765                 # halt at the next controlled stop
```

### Inspect, edit, resume

```bash
python -m aidb status --port 8765               # state, armed breaks, stopped value
python -m aidb inspect --port 8765              # alias for status

python -m aidb edit --port 8765 --content "Revised reply"
python -m aidb edit --port 8765 --value-json '{"order_id":"ORD-1001","amount":"12.34"}'
python -m aidb edit --port 8765 --payload-json '{"content":"Revised reply"}'

python -m aidb continue --port 8765
python -m aidb end --port 8765                  # end the session and stop the run
```

`--content` applies to a model-reply stop. `--value-json` applies to a handoff stop and must be a JSON object. `--payload-json` merges into the stopped payload. Pass only one of them.

A successful command prints JSON on stdout:

```json
{"breaks": ["model_reply"], "ok": true, "state": "halted"}
```

While held, `status` also includes `stop` (`kind`, `run_id`, `payload`). Failures print `error: ...` and exit non-zero.

## Your own agent

Create a session, serve it on localhost, and gate each reply and handoff:

```python
from aidb.server import start_control_server
from aidb.session import DebugSession, SessionEnded

session = DebugSession()
bound = start_control_server(session, host="127.0.0.1", port=8765)
# bound.host, bound.port, bound.token — print the token with the port

try:
    session.gate_before_advance()
    effective = session.gate_after_event(
        "model_reply",  # or "handoff"
        run_id=run_id,
        payload={"content": reply},
    )
    # the next step consumes `effective`
except SessionEnded:
    return
```

`gate_after_event` returns the original payload when that break is off, and the edited payload after `continue`. `end` raises `SessionEnded` from the gate so the run can stop.

Handoff payloads need a non-empty string `target` and an object `value`. Model-reply payloads need a string `content`.

## Security

The control server accepts `127.0.0.1` and `localhost` only. Every command must carry the shared token printed with the port. Keep the control port off public interfaces. This is for local and lower environments where side effects are mocked.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check aidb samples tests
```

### Architecture

```text
aidb/
├── session.py    # halt, break, edit, continue — the in-process gate
├── server.py     # localhost JSON-line control server
├── client.py     # TCP client used by the CLI
└── cli.py        # attach / break / edit / continue
samples/refund_desk/   # mocked multi-agent app that calls the gate
tests/
```

Milestone notes live in [docs/product/agent-debugger/](docs/product/agent-debugger/).
