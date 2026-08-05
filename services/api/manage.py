#!/usr/bin/env python
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    current = Path(__file__).resolve().parent
    for _ in range(4):
        env_file = current / ".env"
        if env_file.is_file():
            load_dotenv(env_file)
            break
        if current.parent == current:
            break
        current = current.parent

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
