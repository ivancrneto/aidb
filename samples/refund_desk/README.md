# Refund desk sample

In-repo multi-agent app for the live-attach milestone (Epic A).

- Two agents: `intake` and `policy`
- One mocked tool: `issue_refund` (in-memory ledger, no network or payment)
- Observable `model_reply` and `handoff` events on stdout
- Optional localhost debug port for attach / halt / continue (TKT-A2 / #10)
- No debugger UI

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
