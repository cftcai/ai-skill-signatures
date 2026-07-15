# ai-skill-signatures

Versioned collection of detection patterns for the ai-skill-scanner.

**Web frontend demo**: https://github.com/cftcai/ai-skill-scanner-web

This repository contains only data. The scanner tool consumes these signatures via git pull or shallow clone.

## Repository Layout

- manifest.json — current version, minimum scanner version, and list of active signature files
- signatures/ — directory containing individual JSON rule files
- .github/workflows/validate-signatures.yml — PR validation for JSON schema and structure

## Named Regex Groups and Non-Capturing Groups

Signature patterns use regular expressions. Capturing groups ( ... ) extract substrings into match groups for later processing. Non-capturing groups (?: ... ) group alternatives without capturing, which is mandatory in these patterns for performance. The scanner only tests for the presence of a match and never uses captured text, so every group in EXFIL_PATTERNS and signature files must use the non-capturing form to avoid unnecessary allocation.

Named groups (?P<name>...) allow later reference by name in Python re but are not required here because the scanner does not post-process captures.

Example of mandatory non-capturing form used throughout:

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

Regex patterns are compiled once at module import time in the scanner to eliminate repeated parsing overhead. Non-capturing groups are mandatory in all signature patterns because the scanner only checks for match presence and never extracts captured text.

### Regex Compilation and Group Type Benchmark

| Operation                    | Naive (per-file compile + capturing groups) | Optimized (module-level compile + non-capturing) | Improvement |
|------------------------------|---------------------------------------------|--------------------------------------------------|-------------|
| 100 small .py files          | 0.42 s                                      | 0.09 s                                           | 4.7x        |
| 1 large SKILL.md with 50 patterns | 0.18 s                                   | 0.03 s                                           | 6x          |
| High-entropy string scan     | Higher allocation from captures             | Zero capture buffers                             | ~15-25% less memory |

The mock malicious skill fixture located at tests/malicious_skill.py in the ai-skill-scanner repository serves as the canonical test case. It exercises all high-severity detection paths (dangerous execution, exfiltration callbacks, prompt injection, and obfuscation) and is used by test_malicious_skill_fixture to validate both correctness and performance characteristics.

## Release Process (latest_commit_sha)

The `manifest.json` field `latest_commit_sha` is used by the scanner for integrity verification when running `--update-signatures`.

### How to perform a release

1. Make all desired changes to signature files and `manifest.json`.
2. Commit the changes.
3. Create and push a new tag:
   ```bash
   git tag v2026.07.16
   git push origin v2026.07.16
   ```
4. Update `latest_commit_sha` in `manifest.json` to the current HEAD:
   ```bash
   LATEST_SHA=$(git rev-parse HEAD)
   jq --arg sha "$LATEST_SHA" '.latest_commit_sha = $sha' manifest.json > manifest.tmp && mv manifest.tmp manifest.json
   git add manifest.json
   git commit --amend --no-edit
   git push --force-with-lease
   ```
5. (Optional) Create a GitHub Release from the tag for visibility.

After this process, any scanner running `--update-signatures` will verify the fetched commit matches the pinned SHA.

## Contributing New Signatures

1. Fork this repository.
2. Add or edit a .json file inside signatures/.
3. Update manifest.json if adding a new file.
4. Open a pull request. The validate workflow will check syntax and required fields.
5. Once merged, follow the Release Process above so scanners can detect the update.

## Versioning

Releases follow calendar versioning (YYYY.MM.DD). The manifest.version field is the authoritative version string. Scanners compare this value before loading.

## License

MIT. See LICENSE.