"""Exit after one no-effect local diagnostic; never consume provider work."""

import asyncio
import json
import os
import sys

from shipsense_local.cli import queue_smoke


def main() -> int:
    if os.environ.get("SHIPSENSE_PROFILE", "local") != "local":
        print(json.dumps({"error": "LOCAL_PROFILE_REQUIRED"}))
        return 2
    if sys.argv[1:] == ["--queue-smoke"]:
        print(json.dumps(asyncio.run(queue_smoke())))
        return 0
    if sys.argv[1:]:
        print(json.dumps({"error": "INVALID_WORKER_ARGUMENT"}))
        return 2
    print(json.dumps({"mode": "local-foundation", "processed": 0, "effects": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
