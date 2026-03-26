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

## Moondream runtime modes

ScreenSentinel uses the `moondream` Python client and reads these optional env vars:

- `MOONDREAM_MODE=local` (default): uses `moondream.vl(local=True)`
- `MOONDREAM_MODE=endpoint`: uses `MOONDREAM_ENDPOINT` (default `http://localhost:2020/v1`)
- `MOONDREAM_MODE=cloud`: uses hosted endpoint with `MOONDREAM_API_KEY`

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
