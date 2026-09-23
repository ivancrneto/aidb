# Refund desk sample

In-repo multi-agent app for the live-attach milestone.

- Two agents: `intake` and `policy`
- One mocked tool: `issue_refund` (in-memory ledger, no network or payment)
- Observable `model_reply` and `handoff` events on stdout
- Optional localhost debug port for attach / halt / break-after-reply / break-on-handoff
  (TKT-A2, TKT-B1, TKT-B2)
- No debugger UI

The control server accepts **127.0.0.1 / localhost only** and requires a **shared token**
on every command (public repo safety). The token is printed on stderr with the port.

```bash
python -m samples.refund_desk
python -m samples.refund_desk --order ORD-2099
```

## Attach and halt (TKT-A2)

Terminal 1 — start a paced live run with a control port:

```bash
python -m samples.refund_desk --debug-port 8765 --pace 2
```

Terminal 2 — use the printed token:

```bash
export AIDB_CONTROL_TOKEN=...   # from stderr
python -m aidb halt --port 8765 --token "$AIDB_CONTROL_TOKEN"
python -m aidb status --port 8765 --token "$AIDB_CONTROL_TOKEN"
python -m aidb continue --port 8765 --token "$AIDB_CONTROL_TOKEN"
```

Or an interactive session:

```bash
python -m aidb attach --port 8765 --token "$AIDB_CONTROL_TOKEN"
```

## Stop after model reply (TKT-B1)

Arm a sticky break so each model reply is held for inspect. Resume without editing
keeps the original reply (editing is a later ticket).

```bash
python -m aidb break-reply --port 8765 --token "$AIDB_CONTROL_TOKEN"
python -m aidb inspect --port 8765 --token "$AIDB_CONTROL_TOKEN"
python -m aidb continue --port 8765 --token "$AIDB_CONTROL_TOKEN"
python -m aidb clear-break-reply --port 8765 --token "$AIDB_CONTROL_TOKEN"
```

## Stop on tool or agent handoff (TKT-B2)

Arm a sticky break so each handoff is held before the tool or nested agent runs.

```bash
python -m aidb break-handoff --port 8765 --token "$AIDB_CONTROL_TOKEN"
python -m aidb inspect --port 8765 --token "$AIDB_CONTROL_TOKEN"
python -m aidb continue --port 8765 --token "$AIDB_CONTROL_TOKEN"
python -m aidb clear-break-handoff --port 8765 --token "$AIDB_CONTROL_TOKEN"
```
