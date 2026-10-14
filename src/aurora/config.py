"""Configuração local compartilhada pela aplicação e pela prova ADK."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    model: str
    data_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(Path.cwd() / ".env")
        return cls(
            model=os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite",
            data_dir=Path(os.getenv("AURORA_DATA_DIR") or "var").resolve(),
        )
