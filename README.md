# ai-skill-signatures

Versioned collection of detection patterns for the ai-skill-scanner.

**Web interface**: https://github.com/cftcai/ai-skill-scanner-web

This repository contains only data. The scanner tool consumes these signatures via git pull or shallow clone.

## Repository Layout

- manifest.json — current version, minimum scanner version, and list of active signature files
- signatures/ — directory containing individual JSON rule files
- .github/workflows/validate-signatures.yml — PR validation for JSON schema and structure

## Non-Capturing Groups

The scanner only tests whether a pattern matches; it never reads captured text. Prefer non-capturing groups `(?: ... )` over capturing groups `( ... )` so the regex engine does not track capture spans it will never use. Named groups `(?P<name>...)` are unnecessary for the same reason.

```json
"pattern": "(?:ignore|override).*?(?:previous|all).*?(?:instructions|rules)"
```

## JSON Schema for Rule Entries

Every object in a signatures/*.json file must contain exactly these fields:

- id (string, required): Unique rule identifier e.g. PI-001
- pattern (string, required): Valid Python re pattern string
- ignorecase (boolean, required): true for case-insensitive match
- severity (string, required): high, medium or low
- description (string, required): Human explanation of the threat
- added_in (string, required): Version or date the rule was added

Optional future fields may include:
- references (array of strings): URLs to advisories, CVEs or test cases

The validate-signatures workflow enforces this schema on every pull request.

## Performance

The scanner compiles each rule once per run — the built-in rules at import time, and the signature rules once when they are loaded from this repository. Compiling the full set is negligible; matching cost dominates and scales with the amount of code scanned.

Measure it yourself with the included, dependency-free harness, which loads every pattern in `signatures/` and times both compilation and line-by-line matching against a synthetic corpus:

```bash
python benchmarks/benchmark.py --lines 100000
```

Illustrative result (7 rules, Python 3.11, a laptop — re-run locally; absolute numbers are machine-dependent):

| Metric | Value |
|---|---|
| Compile all rules (cold) | ~1.1 ms |
| Scan 100,000 lines | ~1.4 s |
| Throughput | ~70,000 lines/sec |

The canonical correctness case is `tests/malicious_skill.py` in the ai-skill-scanner repository, which exercises every high-severity path (dangerous execution, exfiltration callbacks, prompt injection, obfuscation).

## Release Process

Signature updates are published by merging to `main`; scanners pick them up via
shallow clone / `git pull` on their next run.

1. Add or edit files under `signatures/` and update `manifest.json` (bump
   `version`, and add the file to the `signatures` list if it is new). Manifest
   paths are relative to the repository root, e.g.
   `signatures/prompt_injection.json` — this is how the scanner resolves them
   against its local clone.
2. Open a pull request. The **Validate Signatures** workflow checks JSON
   structure, required fields, regex compilability, and that `manifest.json`
   lists exactly the files present on disk.
3. Merge to `main`. Do **not** force-push or otherwise rewrite `main` history:
   scanners fetch with `git pull --ff-only`, which fails on rewritten history
   and causes them to silently fall back to the built-in patterns.
4. (Optional) Tag the release for traceability:
   ```bash
   git tag -a v2026.07.16 -m "Signature release 2026.07.16"
   git push origin v2026.07.16
   ```

### A note on `latest_commit_sha` and integrity

`manifest.json` carries a `latest_commit_sha` field that the scanner compares
against the fetched `HEAD`. It ships as a `PLACEHOLDER…` value, and the scanner
**skips** verification for placeholder values.

Storing the SHA inside this repository cannot by itself provide integrity: an
attacker able to push here controls both `HEAD` and the manifest, so a
self-referential pin verifies nothing. (It is also impractical — a commit cannot
contain its own resulting SHA.) Robust verification must be **client-side**: the
scanner pinning a known-good tag/SHA it trusts, or verifying a maintainer-signed
tag (`git tag -v`). That is tracked as scanner-side work. Until it lands, treat
`latest_commit_sha` as advisory, keep the placeholder, and rely on HTTPS plus a
trusted `main`.

## Contributing New Signatures

1. Fork this repository.
2. Add or edit a .json file inside signatures/.
3. Update manifest.json if adding a new file.
4. Open a pull request. The validate workflow will check syntax and required fields.
5. Once merged to `main`, scanners pick up the change on their next run.

## Versioning

Releases follow calendar versioning (YYYY.MM.DD). The manifest.version field is the authoritative version string. Scanners compare this value before loading.

## License

MIT. See LICENSE.