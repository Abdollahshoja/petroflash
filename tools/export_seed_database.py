"""Export the initial selected component to a versioned JSON file."""

import json
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from petroflash.reference_data import methane


def main():
    document = {
        "schema_version": 1,
        "dataset_version": "0.1.0",
        "description": "Initial selected methane data with provenance.",
        "components": [asdict(methane())],
    }

    text = json.dumps(
        document,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"

    output = PROJECT_ROOT / "data" / "components.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("x", encoding="utf-8") as stream:
        stream.write(text)

    print(f"Created: {output}")
    print(f"Components exported: {len(document['components'])}")


if __name__ == "__main__":
    main()
