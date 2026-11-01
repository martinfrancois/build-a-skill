# Worked example

## Error messages name the thing and the next step

### Not like this

```python
def store_avatar(user_id: str, filename: str, data: bytes) -> str:
    if not filename.lower().endswith((".png", ".jpg")):
        raise ValueError("Invalid file type!")
    if len(data) > MAX_AVATAR_BYTES:
        raise ValueError(f"Error: file too large ({len(data)} bytes).")
    try:
        return bucket.put(f"avatars/{user_id}/{filename}", data)
    except StorageTimeout:
        raise RuntimeError("Failed to upload avatar, sorry") from None
```

### Like this

```python
def store_avatar(user_id: str, filename: str, data: bytes) -> str:
    if not filename.lower().endswith((".png", ".jpg")):
        raise ValueError(f'cannot store avatar "{filename}": expected a .png or .jpg file')
    if len(data) > MAX_AVATAR_BYTES:
        raise ValueError(
            f'cannot store avatar "{filename}": it has {len(data)} bytes, '
            f"the limit is {MAX_AVATAR_BYTES}"
        )
    try:
        return bucket.put(f"avatars/{user_id}/{filename}", data)
    except StorageTimeout as err:
        raise RuntimeError(
            f'cannot upload avatar "{filename}": storage timed out, retry in a minute'
        ) from err
```

Why: the caller sees the message without the code, so it has to say which thing failed and
what to do next.

### What changed

| Message | Change |
|---|---|
| File type | Starts with `cannot store avatar`, quotes the file name, says which types work |
| Size | Drops the `Error:` prefix and trailing period, states the limit next to the actual size |
| Upload | Drops the apology, tells the caller to retry, keeps the timeout as the cause instead of `from None` |

The file name is safe to quote. The user ID would be too, but the message already identifies the
upload by file name, so it stays out to keep the line short.
