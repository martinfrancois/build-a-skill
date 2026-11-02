"""End-of-day closing for one till."""

from datetime import date
from pathlib import Path

from .snapshot import Item


def close_day(items: list[Item], snapshot_dir: Path, day: date) -> Path:
    path = snapshot_dir / f"{day.isoformat()}.csv"
    return path
