"""Reads settings.toml and the API keys in .env."""
import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def settings() -> dict:
    with open(ROOT / "settings.toml", "rb") as f:
        return tomllib.load(f)


def api_key(name: str) -> str:
    """Return an API key from .env (or the environment). Empty string if missing."""
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key.strip() == name:
                    return value.strip().strip('"').strip("'")
    return os.environ.get(name, "")
