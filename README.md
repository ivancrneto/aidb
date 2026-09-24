# aidb

Live-attach debugger for multi-agent apps.

A developer attaches to a live run, stops on a model reply or a handoff (tool or agent), edits that value, and resumes the same run so the next step uses the edit.

This repository is **public**. The debug control plane:

- Binds **localhost only** (`127.0.0.1`)
- Requires a **shared token** on every command (printed with the port; also `AIDB_CONTROL_TOKEN`)

Do not expose the control port on a public interface.

## Sample app

`samples/refund_desk` is a mocked multi-agent refund desk. It is a CLI process. Starting it does not open or require a debugger UI.

```bash
python -m samples.refund_desk
```

### Attach, halt, edit, and resume

```bash
python -m samples.refund_desk --debug-port 8765 --pace 2
# stderr prints port + token
python -m aidb break-reply --port 8765 --token "$TOKEN"
python -m aidb edit --port 8765 --token "$TOKEN" --content "Revised intake reply"
python -m aidb continue --port 8765 --token "$TOKEN"
```

## Tests

```bash
python -m pip install -e ".[dev]"
python -m pytest
```
