import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    "database": {"path": "./data/hebb_db"},
    "hotkeys": {
        "copy": "<ctrl>+<cmd>+c",
        "paste": "<ctrl>+<cmd>+v",
        "delete": "<ctrl>+<cmd>+d"
    },
    "settings": {"decay_on_startup": True, "paste_delay": 0.1}
}

def load_config():
    config_path = Path("config.yaml")
    if not config_path.exists():
        return DEFAULT_CONFIG
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)