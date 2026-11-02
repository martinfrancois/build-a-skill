#!/usr/bin/env bash
# Rebuilds the state at the end of the session: the project committed as it was before the first
# prompt, and the version the user accepted left in the working tree, not yet committed. Tessl
# uploads only declared scenario files, so the accepted version is written from this script.
set -euo pipefail
cd inventory-service
if [ ! -d .git ]; then
  git init -q -b main
  git add -A
  git -c user.name=Dev -c user.email=dev@example.com commit -q -m "Load the morning stock count"
fi
cat > inventory/snapshot.py <<'SESSION_FILE'
"""The stock count each till writes at closing and reads back the next morning."""

import csv
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    quantity: int


def load_snapshot(path: Path) -> list[Item]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [Item(row["sku"], row["name"], int(row["quantity"])) for row in reader]


def save_snapshot(items: list[Item], path: Path) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sku", "name", "quantity"])
        for item in items:
            writer.writerow([item.sku, item.name, item.quantity])
    os.replace(tmp, path)
SESSION_FILE
cat > inventory/closing.py <<'SESSION_FILE'
"""End-of-day closing for one till."""

from datetime import date
from pathlib import Path

from .snapshot import Item, save_snapshot


def close_day(items: list[Item], snapshot_dir: Path, day: date) -> Path:
    path = snapshot_dir / f"{day.isoformat()}.csv"
    save_snapshot(items, path)
    return path
SESSION_FILE
