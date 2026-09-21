# aidb

Live-attach debugger for multi-agent apps.

A developer attaches to a live run, stops on a model reply or a handoff (tool or agent), edits that value, and resumes the same run so the next step uses the edit.

This repository is at the first implementation ticket: an in-repo sample app the later attach workflow can use.

## Sample app

`samples/refund_desk` is a mocked multi-agent refund desk. It is a CLI process. Starting it does not open a debugger UI.

```bash
python -m samples.refund_desk
```

Approved path (default, `ORD-1001`):

- intake agent produces a model reply
- intake hands off to the policy agent
- policy produces a model reply
- policy hands off to the mocked `issue_refund` tool

Denied path:

```bash
python -m samples.refund_desk --order ORD-2099
```

JSON events:

```bash
python -m samples.refund_desk --format json
```

## Tests

```bash
python -m pip install -e ".[dev]"
python -m pytest
```
