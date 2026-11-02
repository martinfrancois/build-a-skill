# orders-service

Takes orders from the shop front end and stores them in PostgreSQL. Start it with
`python -m orders.main`.

## Configuration

The service reads its settings from environment variables at startup.

| Variable | Required | Value |
|---|---|---|
| `PORT` | yes | a whole number from 1 to 65535 |
| `LOG_LEVEL` | yes | `debug`, `info`, `warning`, or `error` |
| `DATABASE_URL` | yes | starts with `postgresql://`, such as `postgresql://app:s3cret@db.internal:5432/orders` |
| `WORKERS` | no, defaults to 4 | a whole number from 1 to 32 |

`load_settings` checks them in this order and raises `ValueError` for the first one that is
missing or invalid.
