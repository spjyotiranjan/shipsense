"""Export deterministic OpenAPI without reading deployment configuration."""

import json
from pathlib import Path
from unittest.mock import patch

from shipsense_api.main import create_app


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    with patch.dict("os.environ", {"SHIPSENSE_PROFILE": "local"}):
        schema = create_app().openapi()
    target = root / "packages/contracts/openapi.json"
    target.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
