Earlier in this session, in `inventory-service/`:

**Me:** Add a `save_snapshot(items, path)` function to `inventory/snapshot.py` that writes the
items as CSV, and call it from `close_day`.

**You:** Added it:

```python
def save_snapshot(items: list[Item], path: Path) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sku", "name", "quantity"])
        for item in items:
            writer.writerow([item.sku, item.name, item.quantity])
```

**Me:** Always give `open` an encoding. The tills run Windows and half the item names have
accents.

**You:** Changed it:

```python
    with open(path, "w", newline="", encoding="utf-8") as f:
```

**Me:** And if a till crashes halfway through, the next morning's load reads half a file. Write it
somewhere else first and swap it in.

**You:** Done:

```python
def save_snapshot(items: list[Item], path: Path) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sku", "name", "quantity"])
        for item in items:
            writer.writerow([item.sku, item.name, item.quantity])
    os.replace(tmp, path)
```

**Me:** Perfect. Turn this into a skill so I don't have to say either of those again. Put it
next to inventory-service.
