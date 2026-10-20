# Validate service settings

Create `settings.py`. Assume Python 3.12 with only the standard library.

Implement:

```python
def load_settings(env: dict[str, str]) -> Settings
```

`env` holds the process environment. Rules:

- `PORT` is required and must be a whole number from 1 to 65535.
- `LOG_LEVEL` is required and must be one of `debug`, `info`, `warning`, or `error`.
- `DATABASE_URL` is required and must start with `postgresql://`, for example
  `postgresql://app:s3cret@db.internal:5432/orders`.
- `WORKERS` is optional, defaults to 4, and must be a whole number from 1 to 32.
- Raise `ValueError` for the first missing or invalid setting, in the order listed above. The
  service prints the message to its startup log, so an operator reading it should know what to
  change.
- Return a frozen dataclass `Settings` with fields `port`, `log_level`, `database_url`, and
  `workers`.
