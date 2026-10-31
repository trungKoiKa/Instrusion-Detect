from pathlib import Path
import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"

def load_config(name):
    with open(CONFIG_DIR / f"{name}.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)