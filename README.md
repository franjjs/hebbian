# 🧠 Hebbian

**Hebbian** is an associative memory tool for your clipboard. Unlike conventional managers that use a simple FIFO queue, Hebbian treats data as nodes in a **Graph Database (KùzuDB)**.

It implements a digital version of **Hebb's Rule**: *"Nodes that fire together, wire together."* The more you use information within a specific context (IDE, Terminal, Browser), the stronger its "synaptic weight" becomes.

## 🚀 Prerequisites (Linux/Ubuntu)

Hebbian requires low-level access to the X11 window system and the clipboard buffer:

```bash
# Install X11 utilities and clipboard bridge
sudo apt-get update
sudo apt-get install x11-utils xclip

## Environment Setup

Hebbian uses `uv` to ensure a reproducible environment across different machines.

```bash
# 1. Enter the project directory
cd hebbian

# 2. Pin the Python version to 3.12 (uv will download it if missing)
uv python pin 3.12

# 3. Sync dependencies and setup the virtual environment
uv sync


udo apt install rofi

