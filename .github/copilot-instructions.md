# Copilot Instructions for Hebbian

## Project Overview
- **Hebbian** is an associative clipboard manager using a graph database (KùzuDB) to model memory as nodes and context as relationships, inspired by Hebb's Rule: "Nodes that fire together, wire together."
- Data is ingested from the clipboard and associated with the active application context (e.g., IDE, Terminal, Browser). The more often a piece of data is used in a context, the stronger its "synaptic weight."

## Key Components
- `src/hebbian/brain.py`: Core logic for interacting with the KùzuDB database. Handles schema, strengthening associations, and smart recall.
- `src/hebbian/main.py`: Entrypoint for hotkey handling, clipboard ingestion, and context-aware paste.
- `src/hebbian/utils.py`: Determines the active window/application context using X11 utilities.
- `src/hebbian/config.py` & `config.yaml`: Loads and manages configuration (database path, hotkeys, settings).
- `data/`: Stores the persistent KùzuDB database file.

## Developer Workflows
- **Environment:** Uses Python 3.12, managed and pinned with `uv` for reproducibility.
- **Setup:**
  - Install system dependencies: `sudo apt-get install x11-utils xclip rofi`
  - Pin Python: `uv python pin 3.12`
  - Sync dependencies: `uv sync`
- **Run:**
  - Use the script entrypoint: `python -m hebbian.main` or the CLI `hebb` if installed as a package.
- **Configuration:**
  - Edit `config.yaml` for database path, hotkeys, and settings. Defaults are in `src/hebbian/config.py`.

## Patterns & Conventions
- **Clipboard ingestion** is always context-aware: see `on_hebb_copy()` in `main.py`. **Weight is incremented only when a memory is pasted, not when copied.**
- **Database schema** is auto-initialized if missing; see `_init_schema()` in `brain.py`.
- **Hotkeys** are defined in config and handled via `pynput`.
- **Context detection** relies on X11 and may return "Unknown-Context" if detection fails.
- **No tests** or CI/CD scripts are present by default.

## Integration Points
- **KùzuDB**: Used for all data storage and retrieval. See `brain.py` for query patterns.
- **X11 utilities**: Required for clipboard and window context access.

## Examples
- To add a new context type, extend `get_active_window_context()` in `utils.py`.
- To change hotkeys, update `config.yaml` and ensure the handler in `main.py` matches.

---
For more details, see the [README.md](../../README.md) and source files in `src/hebbian/`.
