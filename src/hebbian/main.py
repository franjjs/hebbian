
import pyperclip
import time
import subprocess
import numpy as np
from pynput import keyboard
from pynput.keyboard import Controller, Key

from hebbian.brain import HebbianBrain
from hebbian.utils import get_active_window_context
from hebbian.config import load_config

config = load_config()
kb_controller = Controller()
brain = HebbianBrain()

def on_hebb_copy():
    """Super+Alt+C: Copy and ingest clipboard."""
    time.sleep(0.05)  # Release key bus
    with kb_controller.pressed(Key.ctrl):
        kb_controller.tap('c')
        time.sleep(0.05)
    time.sleep(0.3)  # Wait for clipboard update
    content = pyperclip.paste()
    if content:
        ctx = get_active_window_context()
        brain.strengthen(content, ctx)
        log_preview = content.replace('\n', ' ').strip()[:50]
        print(f"📥 [Ingested] From: {ctx:<15} | Data: {log_preview}...")
    else:
        print("⚠️ Warning: Clipboard empty.")


def get_reference_text():
    """Get selected text (X11 PRIMARY) or clipboard."""
    try:
        # Suppress unwanted error output from xclip by redirecting stderr to /dev/null
        sel_text = subprocess.check_output(
            ['xclip', '-selection', 'primary', '-o'],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        sel_text = ''
    # If selection is not available, fallback to clipboard
    if not sel_text:
        return pyperclip.paste()
    return sel_text

def parse_embedding(emb_str, ref_emb):
    if not emb_str:
        return np.zeros_like(ref_emb)
    return np.array([float(x) for x in emb_str.split(',')])

def cosine_sim(a, b):
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return -1
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def select_memory(menu_options, ctx):
    """Select memory using Rofi (can be replaced)."""
    input_str = "\n".join(menu_options)
    try:
        proc = subprocess.Popen(
            ['rofi', '-dmenu', '-p', f'Hebb ({ctx})', '-format', 'i', '-i'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
        )
        stdout, _ = proc.communicate(input=input_str)
        if stdout.strip():
            return int(stdout.strip())
        else:
            return None
    except Exception as e:
        print(f"❌ Selection error: {e}")
        return None

def on_hebb_paste():
    ctx = get_active_window_context()
    memories = brain.recall_smart(ctx)
    if not memories:
        print("⚠️ No memories to paste.")
        return

    # Sort by embedding similarity to selected text or clipboard
    ref_text = get_reference_text()
    model = brain.model
    ref_emb = model.encode(ref_text) if ref_text else None
    if ref_emb is not None:
        for m in memories:
            m['sim'] = cosine_sim(ref_emb, parse_embedding(m.get('embedding'), ref_emb))
        memories.sort(key=lambda m: m.get('sim', -1), reverse=True)

    menu_options = []
    for m in memories:
        tag = "[ctx]" if m['is_context'] else "[glob]"
        preview = m['content'].replace('\n', ' ').strip()[:60]
        emb_short = ''
        if m.get('embedding'):
            emb_list = m['embedding'].split(',')
            emb_short = ','.join(emb_list[:3])
        sim_str = f" S:{m['sim']:.2f}" if 'sim' in m else ''
        menu_options.append(f"{tag} (W:{m['weight']}) (E:{emb_short}){sim_str} {preview}")

    idx = select_memory(menu_options, ctx)
    if idx is not None:
        full_content = memories[idx]['content']
        brain.increment_weight(full_content, ctx)
        pyperclip.copy(full_content)
        time.sleep(0.1)
        with kb_controller.pressed(Key.ctrl):
            kb_controller.tap('v')
        print(f"📤 [Pasted] Context: {ctx}")

def on_hebb_delete():
    brain.clear_all_memories()
    print("🗑️ All memories deleted.")

def main():
    print(f"--- Hebbian Daemon Started ---")
    with keyboard.GlobalHotKeys({
        config["hotkeys"]["copy"]: on_hebb_copy,
        config["hotkeys"]["paste"]: on_hebb_paste,
        config["hotkeys"]["delete"]: on_hebb_delete
    }) as h:
        h.join()

if __name__ == "__main__":
    main()
