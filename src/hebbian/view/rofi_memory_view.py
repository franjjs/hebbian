import subprocess
import logging
from hebbian.view.memory_view import MemoryView

class RofiMemoryView(MemoryView):
    def select(self, options, context):
        input_str = "\n".join(options)
        try:
            proc = subprocess.Popen(
                ['rofi', '-dmenu', '-p', f'Hebb ({context})', '-format', 'i', '-i'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
            )
            stdout, _ = proc.communicate(input=input_str)
            if stdout.strip():
                return int(stdout.strip())
            else:
                return None
        except Exception as e:
            logging.error(f"Selection error: {e}")
            return None

