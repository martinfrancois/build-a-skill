# Review the payment webhook

Use $my-skill to review the error handling in `webhook.py` below and write your findings to
`review.md`. Assume Python 3.12. Keep the code's behavior as it is; the review is about what
it reports when something goes wrong.

```python
import hmac
import logging

log = logging.getLogger(__name__)


def handle_webhook(payload: dict, signature: str, secret: str, gateway) -> None:
    expected = hmac.new(secret.encode(), payload["body"].encode(), "sha256").hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("Invalid signature!")

    event_type = payload.get("type")
    if event_type not in ("charge.succeeded", "charge.failed"):
        raise ValueError(f"Error: unknown event type {event_type}")

    card_number = payload["card"]["number"]
    try:
        gateway.capture(payload["charge_id"])
    except TimeoutError as err:
        log.error("Failed to capture charge for card %s using key %s", card_number, gateway.api_key)
        raise RuntimeError("Something went wrong.") from None
```
