# Refund desk sample

In-repo multi-agent app for the live-attach milestone (TKT-A1 / #9).

- Two agents: `intake` and `policy`
- One mocked tool: `issue_refund` (in-memory ledger, no network or payment)
- Observable `model_reply` and `handoff` events on stdout
- No debugger UI

```bash
python -m samples.refund_desk
python -m samples.refund_desk --order ORD-2099
```
