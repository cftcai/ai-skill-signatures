#!/usr/bin/env python3
"""Validate manifest.json and all signature files."""
import json
import sys
from pathlib import Path


def validate_manifest(manifest_path: Path) -> None:
    if not manifest_path.exists():
        print(f"ERROR: {manifest_path} not found")
        sys.exit(1)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: {manifest_path} is not valid JSON: {e}")
        sys.exit(1)

    required = {"version", "minimum_scanner_version", "signatures", "latest_commit_sha"}
    if not required.issubset(manifest.keys()):
        print(f"ERROR: {manifest_path} missing required fields: {required - manifest.keys()}")
        sys.exit(1)
    print("\u2713 manifest.json structure is valid")


def validate_signature_file(path: Path) -> None:
    if not path.exists():
        print(f"ERROR: Signature file not found: {path}")
        sys.exit(1)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} is not valid JSON: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print(f"ERROR: {path} must contain a JSON array")
        sys.exit(1)

    required_keys = {"id", "pattern", "ignorecase", "severity", "description", "added_in"}
    for entry in data:
        missing = required_keys - entry.keys()
        if missing:
            print(f"ERROR: {path} missing keys {missing} in entry {entry.get('id', 'unknown')}")
            sys.exit(1)
    print(f"\u2713 {path.name} is valid")


def main() -> None:
    root = Path(".")
    manifest_path = root / "manifest.json"

    validate_manifest(manifest_path)

    signatures_dir = root / "signatures"
    if not signatures_dir.exists():
        print(f"ERROR: {signatures_dir} directory not found")
        sys.exit(1)

    # Validate every signature file
    for sig_file in sorted(signatures_dir.glob("*.json")):
        validate_signature_file(sig_file)

    # Check that manifest lists every file
    try:
        listed = set(json.loads(manifest_path.read_text(encoding="utf-8"))["signatures"])
    except (KeyError, json.JSONDecodeError) as e:
        print(f"ERROR: Could not read signatures list from manifest: {e}")
        sys.exit(1)

    on_disk = {f.name for f in signatures_dir.glob("*.json")}
    missing = on_disk - listed
    if missing:
        print(f"ERROR: Files missing from manifest.json: {missing}")
        sys.exit(1)
    print("\u2713 All signature files are listed in manifest.json")


if __name__ == "__main__":
    main()
