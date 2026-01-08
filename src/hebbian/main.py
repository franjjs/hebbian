import pyperclip
import time
import subprocess
import logging
from pynput import keyboard
from pynput.keyboard import Controller, Key

from hebbian.brain import HebbianBrain
from hebbian.utils import get_active_window_context
from hebbian.config import load_config
from hebbian.view.rofi_memory_view import RofiMemoryView

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)


config = load_config()
kb_controller = Controller()
brain = HebbianBrain()
memory_view = RofiMemoryView()

def on_hebb_copy():
    """Copy and ingest clipboard."""
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
        logging.info(f"[Ingested] From: {ctx:<15} | Data: {log_preview}...")
    else:
        logging.warning("Warning: Clipboard empty.")


def on_hebb_paste():
    """Recall and paste memory."""
    ctx = get_active_window_context()
    memories = brain.recall_smart(ctx)
    if not memories:
        logging.warning("No memories to paste.")
        return

    ref_text = get_reference_text()
    menu_options = prepare_menu_options(memories, ref_text, brain.embedding_store)

    idx = memory_view.select(menu_options, ctx)
    if idx is not None:
        full_content = memories[idx]['content']
        brain.increment_weight(full_content, ctx)
        pyperclip.copy(full_content)
        time.sleep(0.1)
        with kb_controller.pressed(Key.ctrl):
            kb_controller.tap('v')
        logging.info(f"[Pasted] Context: {ctx}")

def get_reference_text():
    """Get selected text (X11 PRIMARY) or clipboard."""
    try:
        sel_text = subprocess.check_output(
            ['xclip', '-selection', 'primary', '-o'],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        sel_text = ''

    if not sel_text:
        return pyperclip.paste()
    return sel_text

def prepare_menu_options(memories, ref_text, embedding_store):
    ref_emb = embedding_store.encode(ref_text) if ref_text else None
    if ref_emb is not None:
        for m in memories:
            m['sim'] = embedding_store.similarity(ref_emb, m.get('embedding'))
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
    return menu_options

def on_hebb_delete():
    brain.clear_all_memories()
    logging.info("All memories deleted.")

def main():
    logging.info("Hebbian Daemon Started")
    with keyboard.GlobalHotKeys({
        config["hotkeys"]["copy"]: on_hebb_copy,
        config["hotkeys"]["paste"]: on_hebb_paste,
        config["hotkeys"]["delete"]: on_hebb_delete
    }) as h:
        h.join()

if __name__ == "__main__":
    main()
