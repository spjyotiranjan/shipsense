"""Exit after one no-effect local diagnostic; never consume provider work."""

import json
import os


def main() -> int:
    if os.environ.get("SHIPSENSE_PROFILE", "local") != "local":
        print(json.dumps({"error": "LOCAL_PROFILE_REQUIRED"}))
        return 2
    print(json.dumps({"mode": "local-foundation", "processed": 0, "effects": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
