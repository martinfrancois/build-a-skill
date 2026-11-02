import os
import sys

from orders.settings import load_settings


def main() -> None:
    try:
        settings = load_settings(dict(os.environ))
    except ValueError as err:
        print(f"orders-service did not start: {err}", file=sys.stderr)
        sys.exit(1)
    print(f"orders-service listening on port {settings.port} with {settings.workers} workers")


if __name__ == "__main__":
    main()
