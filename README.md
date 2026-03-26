# ScreenSentinel

CLI accountability tool that captures your screen every 30 seconds, checks if you are on-task with a local Moondream vision model, and calls out drift in real-time.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Install local vision support:

```bash
pip install -e ".[vision]"
```

Run a session:

```bash
screensentinel start --goal "I'm building ScreenSentinel for 2 hours" --duration-min 120
```

Optional flags:

- `--interval-sec` (default: `30`)
- `--strictness` (`lenient|normal|strict`, default: `normal`)
- `--debug-save-captures` (store screenshot files)
- `--db-path` (default: `data/screensentinel.db`)

## Development checks

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m build
```

CI runs the same checks on every push and pull request.
