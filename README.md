# ScreenSentinel

ScreenSentinel is a CLI accountability app that captures your screen every 30 seconds, checks if you are still on-task, sends a notification when you drift, and writes a session report to SQLite.

## What It Does (MVP)

- Screen capture with `mss`
- Vision-based on-task check
- Drift notification with `plyer`
- Session + drift logging in SQLite
- End-of-session CLI report with `rich`

## Quick Start (Fully Local, No API Keys)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# start ollama in another terminal
ollama serve

# one-time model pull
ollama pull llava:7b

# tell ScreenSentinel to use local ollama vision
export SCREENSENTINEL_VISION_BACKEND=ollama
export OLLAMA_VISION_MODEL=llava:7b

# run a test session
screensentinel start --goal "I'm building ScreenSentinel for 10 minutes" --duration-min 10
```

Note: the first sample can take longer while the vision backend warms up.

## CLI Usage

```bash
screensentinel start --goal "I'm building ScreenSentinel" --duration-min 120
```

Optional flags:

- `--interval-sec` (default: `30`)
- `--strictness` (`lenient|normal|strict`, default: `normal`)
- `--debug-save-captures` (keep screenshots in `data/captures/`)
- `--db-path` (default: `data/screensentinel.db`)

## Vision Backends

### 1) Ollama (recommended, fully local/free)

```bash
export SCREENSENTINEL_VISION_BACKEND=ollama
export OLLAMA_VISION_MODEL=llava:7b
```

Optional:

```bash
export OLLAMA_ENDPOINT=http://127.0.0.1:11434/api/generate
```

### 2) Moondream Python client

Install:

```bash
pip install -e ".[vision]"
```

Runtime modes:

- `MOONDREAM_MODE=local` (default)
- `MOONDREAM_MODE=endpoint` + `MOONDREAM_ENDPOINT`
- `MOONDREAM_MODE=cloud` + `MOONDREAM_API_KEY`

If local mode fails with a gated Hugging Face repo, either request access and login (`huggingface-cli login`) or use Ollama backend.

## Data and Output

- SQLite DB: `data/screensentinel.db`
- Optional debug screenshots: `data/captures/`

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Build package:

```bash
python3 -m build
```

CI runs tests + build on every push and PR.
