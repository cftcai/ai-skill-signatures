#!/usr/bin/env python3
"""Unit tests for validate_signatures.py"""
import json
import sys
import tempfile
from pathlib import Path
import pytest

sys_path = Path(__file__).parent.parent
sys.path.insert(0, str(sys_path))
from scripts.validate_signatures import (
    validate_manifest,
    validate_signature_file,
    main as validate_main
)


def test_validate_manifest_valid(tmp_path):
    manifest = {
        "version": "2026.07.15",
        "minimum_scanner_version": "1.1.0",
        "latest_commit_sha": "abc123",
        "signatures": ["test.json"]
    }
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps(manifest))
    validate_manifest(manifest_file)


def test_validate_manifest_missing_fields(tmp_path):
    manifest = {"version": "2026.07.15"}
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps(manifest))
    with pytest.raises(SystemExit):
        validate_manifest(manifest_file)


def test_validate_manifest_invalid_json(tmp_path):
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text("{invalid json}")
    with pytest.raises(SystemExit):
        validate_manifest(manifest_file)


def test_validate_signature_file_valid(tmp_path):
    sig = [{
        "id": "TEST-001",
        "pattern": "test",
        "ignorecase": True,
        "severity": "high",
        "description": "Test",
        "added_in": "2026.07.15"
    }]
    sig_file = tmp_path / "test.json"
    sig_file.write_text(json.dumps(sig))
    validate_signature_file(sig_file)


def test_validate_signature_file_missing_keys(tmp_path):
    sig = [{"id": "TEST-001"}]
    sig_file = tmp_path / "test.json"
    sig_file.write_text(json.dumps(sig))
    with pytest.raises(SystemExit):
        validate_signature_file(sig_file)


def test_main_missing_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        validate_main()


def test_main_missing_signatures_dir(tmp_path, monkeypatch):
    manifest = {
        "version": "2026.07.15",
        "minimum_scanner_version": "1.1.0",
        "latest_commit_sha": "abc123",
        "signatures": []
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        validate_main()


def test_validate_signature_file_bad_regex(tmp_path):
    sig = [{
        "id": "TEST-002",
        "pattern": "(unclosed[group",
        "ignorecase": True,
        "severity": "high",
        "description": "Invalid regex",
        "added_in": "2026.07.16"
    }]
    sig_file = tmp_path / "test.json"
    sig_file.write_text(json.dumps(sig))
    with pytest.raises(SystemExit):
        validate_signature_file(sig_file)


def test_main_valid_with_prefixed_paths(tmp_path, monkeypatch):
    """A manifest listing repo-root-relative paths must validate cleanly."""
    sigs_dir = tmp_path / "signatures"
    sigs_dir.mkdir()
    (sigs_dir / "rules.json").write_text(json.dumps([{
        "id": "TEST-003",
        "pattern": "eval\\(",
        "ignorecase": True,
        "severity": "high",
        "description": "Test rule",
        "added_in": "2026.07.16"
    }]))
    manifest = {
        "version": "2026.07.16",
        "minimum_scanner_version": "1.1.0",
        "latest_commit_sha": "PLACEHOLDER",
        "signatures": ["signatures/rules.json"]
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.chdir(tmp_path)
    validate_main()  # must not raise


def test_main_rejects_stale_manifest_entry(tmp_path, monkeypatch):
    """A manifest listing a file that does not exist must fail."""
    sigs_dir = tmp_path / "signatures"
    sigs_dir.mkdir()
    (sigs_dir / "rules.json").write_text(json.dumps([{
        "id": "TEST-004",
        "pattern": "x",
        "ignorecase": True,
        "severity": "low",
        "description": "Test rule",
        "added_in": "2026.07.16"
    }]))
    manifest = {
        "version": "2026.07.16",
        "minimum_scanner_version": "1.1.0",
        "latest_commit_sha": "PLACEHOLDER",
        "signatures": ["signatures/rules.json", "signatures/missing.json"]
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        validate_main()
