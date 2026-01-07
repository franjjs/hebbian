import pyperclip
import time
import subprocess
from pynput import keyboard
from pynput.keyboard import Controller, Key

from hebbian.brain import HebbianBrain
from hebbian.utils import get_active_window_context
from hebbian.config import load_config

config = load_config()
kb_controller = Controller()
brain = HebbianBrain()

def on_hebb_copy():
    """Triggered by Super+Alt+C: Forces a copy and then ingests."""
    # 1. Breve pausa para liberar el bus de teclado si las teclas físicas siguen pulsadas
    time.sleep(0.05)
    
    # 2. Simulamos el Ctrl+C para que la app (Firefox, Gedit, etc.) mande el texto al clipboard
    with kb_controller.pressed(Key.ctrl):
        kb_controller.tap('c')
        time.sleep(0.05)
    
    # 3. Pausa crucial para que el Sistema Operativo actualice el buffer del portapapeles
    time.sleep(0.3) 
    
    # 4. Ahora leemos lo que hay en el portapapeles
    content = pyperclip.paste()
    
    if content:
        ctx = get_active_window_context()
        brain.strengthen(content, ctx)
        log_preview = content.replace('\n', ' ').strip()[:50]
        print(f"📥 [Ingested] From: {ctx:<15} | Data: {log_preview}...")
    else:
        print("⚠️ Warning: No text selected or clipboard empty.")

def on_hebb_paste():
    ctx = get_active_window_context()
    memories = brain.recall_smart(ctx)
    
    if not memories:
        print("⚠️ No memories to paste.")
        return

    # Create menu for Rofi
    menu_options = []
    for m in memories:
        tag = "[ctx]" if m['is_context'] else "[glob]"
        preview = m['content'].replace('\n', ' ').strip()[:90]
        menu_options.append(f"{tag} (W:{m['weight']}) {preview}")

    input_str = "\n".join(menu_options)
    
    try:
        # Use Rofi in dmenu mode to force custom list selection
        proc = subprocess.Popen(
            ['rofi', '-dmenu', '-p', f'Hebb ({ctx})', '-format', 'i', '-i'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
        )
        stdout, _ = proc.communicate(input=input_str)
        
        if stdout.strip():
            idx = int(stdout.strip())
            full_content = memories[idx]['content']
            # Increment weight on paste
            brain.increment_weight(full_content, ctx)
            pyperclip.copy(full_content)
            time.sleep(0.1)
            with kb_controller.pressed(Key.ctrl):
                kb_controller.tap('v')
            print(f"📤 [Pasted] Context: {ctx}")
    except Exception as e:
        print(f"❌ Selection error: {e}")

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
