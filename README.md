# aidb

Live-attach debugger for multi-agent apps.

A developer attaches to a live run, stops on a model reply or a handoff (tool or agent), edits that value, and resumes the same run so the next step uses the edit.

This repository is **public**. The debug control plane binds **localhost only** (`127.0.0.1`). Do not expose the control port on a public interface.

## Sample app

`samples/refund_desk` is a mocked multi-agent refund desk. It is a CLI process. Starting it does not open or require a debugger UI.

```bash
python -m samples.refund_desk
```

### Attach, halt, and stop after a model reply

Start the sample with a localhost control port, then from another terminal:

```bash
python -m samples.refund_desk --debug-port 8765 --pace 2
python -m aidb break-reply --port 8765
python -m aidb status --port 8765   # includes stop.payload when held after a reply
python -m aidb continue --port 8765
```

## Tests

```bash
python -m pip install -e ".[dev]"
python -m pytest
```
