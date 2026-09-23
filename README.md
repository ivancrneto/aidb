# aidb

Live-attach debugger for multi-agent apps.

A developer attaches to a live run, stops on a model reply or a handoff (tool or agent), edits that value, and resumes the same run so the next step uses the edit.

## Sample app

`samples/refund_desk` is a mocked multi-agent refund desk. It is a CLI process. Starting it does not open or require a debugger UI.

```bash
python -m samples.refund_desk
```

### Attach and halt

Start the sample with a localhost control port, then halt or continue from another terminal:

```bash
python -m samples.refund_desk --debug-port 8765 --pace 2
python -m aidb halt --port 8765
python -m aidb continue --port 8765
```

## Tests

```bash
python -m pip install -e ".[dev]"
python -m pytest
```
