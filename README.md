# ai-skill-signatures

Versioned collection of detection patterns for the ai-skill-scanner.

This repository contains only data. The scanner tool consumes these signatures via git pull or shallow clone.

## Repository Layout

- manifest.json — current version, minimum scanner version, and list of active signature files
- signatures/ — directory containing individual JSON rule files
- .github/workflows/validate-signatures.yml — PR validation for JSON schema and structure

## Contributing New Signatures

1. Fork this repository.
2. Add or edit a .json file inside signatures/.
3. Update manifest.json if adding a new file.
4. Open a pull request. The validate workflow will check syntax and required fields.
5. Once merged, tag a new release so scanners can detect the update.

Each signature entry must include: id, pattern, ignorecase, severity (high/medium/low), description, added_in.

See signatures/prompt_injection.json for the exact schema.

## Versioning

Releases follow calendar versioning (YYYY.MM.DD). The manifest.version field is the authoritative version string.

## License

MIT. See LICENSE.