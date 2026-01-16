#!/usr/bin/env python3
"""Convert a JSON file to YAML format."""

import json
import yaml
import sys
from pathlib import Path


def json_to_yaml(json_path: str, yaml_path: str | None = None) -> None:
    """Convert a JSON file to YAML format.

    Args:
        json_path: Path to the input JSON file.
        yaml_path: Path to the output YAML file. If not provided,
                   uses the same name with .yaml extension.
    """
    json_path = Path(json_path)

    if yaml_path is None:
        yaml_path = json_path.with_suffix(".yaml")
    else:
        yaml_path = Path(yaml_path)

    with open(json_path, "r") as f:
        data = json.load(f)

    with open(yaml_path, "w") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    print(f"Converted {json_path} -> {yaml_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python json_to_yaml.py <input.json> [output.yaml]")
        sys.exit(1)

    json_file = sys.argv[1]
    yaml_file = sys.argv[2] if len(sys.argv) > 2 else None
    json_to_yaml(json_file, yaml_file)
