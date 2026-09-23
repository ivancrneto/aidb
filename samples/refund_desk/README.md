# Refund desk sample

In-repo multi-agent app for the live-attach milestone.

- Two agents: `intake` and `policy`
- One mocked tool: `issue_refund` (in-memory ledger, no network or payment)
- Observable `model_reply` and `handoff` events on stdout
- Optional localhost debug port for attach / halt / break-after-reply (TKT-A2, TKT-B1)
- No debugger UI

The control server accepts **127.0.0.1 / localhost only** (public repo safety).

```bash
python -m samples.refund_desk
python -m samples.refund_desk --order ORD-2099
```

## Attach and halt (TKT-A2)

Terminal 1 — start a paced live run with a control port:

```bash
python -m samples.refund_desk --debug-port 8765 --pace 2
```

Terminal 2 — attach and halt before the next model reply or handoff:

```bash
python -m aidb halt --port 8765
python -m aidb status --port 8765
python -m aidb continue --port 8765
```

Or an interactive session:

```bash
python -m aidb attach --port 8765
```

## Stop after model reply (TKT-B1)

Arm a sticky break so each model reply is held for inspect. Resume without editing
keeps the original reply (editing is a later ticket).

```bash
python -m aidb break-reply --port 8765
python -m aidb inspect --port 8765
python -m aidb continue --port 8765
python -m aidb clear-break-reply --port 8765
```
