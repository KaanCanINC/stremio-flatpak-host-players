#!/usr/bin/env python3
"""Yamayi geri alir: apply.py'nin aldigi yedegi geri yukler."""

import subprocess
import sys

APP_ID = "com.stremio.Stremio"


def main() -> int:
    out = subprocess.run(
        ["flatpak", "info", "--show-location", APP_ID],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    path = out + "/files/libexec/stremio/server.js"
    backup = path + ".stremio-host-players.bak"
    try:
        with open(backup, encoding="utf-8") as f:
            orig = f.read()
    except FileNotFoundError:
        print(f"Yedek bulunamadi: {backup}")
        return 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(orig)
    print(f"Geri alindi: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
