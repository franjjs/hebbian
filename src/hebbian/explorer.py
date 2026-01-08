
import sys
import shutil
import tempfile
from pathlib import Path

from hebbian.memory.kuzu_memory_store import KuzuMemoryStore

def explore():

    db_name = "hebb_db"
    data_dir = Path("./data")
    original_db_path = data_dir / db_name

    if not original_db_path.exists():
        print("DB not found.")
        return

    args = sys.argv[1:]
    show_full = "--full" in args
    search_term = next((a for a in args if a != "--full"), None)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_db_path = Path(tmpdir) / db_name
        try:
            for f in data_dir.glob(f"{db_name}*"):
                shutil.copy2(f, Path(tmpdir) / f.name)

            store = KuzuMemoryStore(db_path=str(temp_db_path), read_only=True)
            print(f"\nHEBBIAN EXPLORER")

            if search_term:
                results = store.search_globally(search_term)
                data = {}
                for r in results:
                    data.setdefault(r[0], []).append({"content": r[1], "weight": r[2]})
            else:
                data = store.get_full_graph_summary()

            for ctx, items in data.items():
                print(f"\nAPP: {ctx}")
                for i, m in enumerate(items, 1):
                    if show_full:
                        print(f"  {i}. [W:{m['weight']}]\n{m['content']}\n" + "-"*20)
                    else:
                        print(f"  {i}. [W:{m['weight']}] {m['content'].strip()[:70]}...")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    explore()
