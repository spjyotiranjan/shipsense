"""Export deterministic OpenAPI without reading deployment configuration."""

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from shipsense_api.main import create_app


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "packages/contracts/openapi.json")
    args = parser.parse_args()
    with patch.dict("os.environ", {"SHIPSENSE_PROFILE": "local"}):
        schema = create_app().openapi()
    target = args.output
    target.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
