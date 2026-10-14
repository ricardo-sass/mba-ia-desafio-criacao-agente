"""Comandos locais do Aurora."""

import argparse

from aurora.config import Settings
from aurora.storage import Storage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["reset", "serve"])
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.command == "reset":
        Storage(settings.data_dir).reset()
        for suffix in ("", "-wal", "-shm"):
            (settings.data_dir / ("sessoes.sqlite3" + suffix)).unlink(missing_ok=True)
        print("Dados restaurados; sessões e pendências removidas; códigos preservados.")
    else:
        import uvicorn

        uvicorn.run(
            "aurora.api:create_app",
            factory=True,
            host="127.0.0.1",
            port=8000,
            workers=1,
        )


if __name__ == "__main__":
    main()
