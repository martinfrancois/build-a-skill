"""The stock count each till writes at closing and reads back the next morning."""

import csv
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
