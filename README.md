# 🧠 Hebbian

**Hebbian** is a semantic, context-aware clipboard manager for Linux. Unlike FIFO clipboard tools, Hebbian models clipboard data as nodes in a **Graph Database (KùzuDB)**, with context as relationships. It supports:

- **Semantic recall**: Uses sentence-transformer embeddings to rank and recall clipboard memories by meaning, not just text.
- **Context-aware memory**: Associates clipboard entries with the active application (IDE, Terminal, Browser, etc.).
- **TTL expiration**: Memories expire after a configurable time-to-live (TTL, in seconds), ensuring privacy and relevance.
- **Local operation**: All data and embeddings are stored locally; no cloud required.
- **Linux-native**: Uses X11 utilities (`xclip`) for clipboard/selection and `rofi` for menu selection, communicating via PIPE for robust, decoupled UI.

It implements a digital version of **Hebb's Rule**: *"Nodes that fire together, wire together."* The more you use information within a specific context, the stronger its "synaptic weight" becomes.

## 🚀 Prerequisites & Setup (Linux/Ubuntu)

Hebbian requires X11 clipboard access and a selector UI:

```bash
# Install X11 utilities and clipboard bridge
sudo apt-get update
sudo apt-get install x11-utils xclip rofi

# Environment Setup
cd hebbian
uv python pin 3.12
uv sync
```

## Features

- **Copy multiple items**: Use the configured hotkey to ingest clipboard data with context.
- **Paste with semantic ranking**: When pasting, Hebbian uses embeddings to rank memories by similarity to the current selection or clipboard.
- **TTL (Time-to-Live)**: Set `ttl` in `config.yaml` to control how long memories persist (in seconds).
- **Selector decoupling**: Uses `rofi` in dmenu mode via PIPE, making it easy to swap out for other selectors in the future.

## Configuration

Edit `config.yaml` to set database path, hotkeys, and TTL. Example:

```yaml
database:
  path: "./data/hebb_db"
hotkeys:
  copy: "<ctrl>+<cmd>+c"
  paste: "<ctrl>+<cmd>+v"
  delete: "<ctrl>+<cmd>+d"
settings:
  ttl: 600
```

## Usage

- Start the daemon: `uv run hebb` or `python -m hebbian.main`
- Copy with hotkey, paste with semantic recall, delete all memories with the delete hotkey.

## Explorer Utility

Hebbian includes a database explorer utility to query and visualize stored memories:

### Command Line Usage

If you install the package with `uv pip install -e .` or have it in your environment, you can run:

```bash
uv run explorer [--full] [search_term]
```

Or, if the script is installed as a global command:

```bash
explorer [--full] [search_term]
```

- `--full`: Shows the full content of each memory.
- `search_term`: Filters memories by the given search term in their content.

### Example

```bash
explorer --full
explorer permission
```

This will display all stored memories grouped by context, or only those matching the search term.

---
For more details, see the source files in `src/hebbian/`.

