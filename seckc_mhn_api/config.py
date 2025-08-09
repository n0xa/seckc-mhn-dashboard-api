"""Simple Base API config loader"""
import os
import yaml
from pathlib import Path

HOME = os.environ.get("HOME", "/tmp")
CONFIG_PATH = Path(HOME) / "data" / "seckc_mhn_api" / "shared" / "config" / "settings.yaml"

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        SETTINGS = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Config file not found: {CONFIG_PATH}")
    SETTINGS = {
        "hpfeeds": {"host": "localhost", "port": 10000, "channels": [], "user": "", "token": ""},
        "mnemosyne": {"username": "", "password": ""},
        "mhn": {"apikey": ""}
    }