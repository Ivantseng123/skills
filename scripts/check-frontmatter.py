#!/usr/bin/env python3
"""Validate YAML frontmatter across the repo.

Catches the failure mode where a plain (unquoted) scalar value contains a
`: ` (colon + space), which YAML reads as a mapping indicator and rejects with
"mapping values are not allowed in this context" — the same error Claude Code's
skill loader surfaces.

Also enforces the AGENTS.md rule that every SKILL.md frontmatter carries
`name`, `description`, and `license`.

Exit code is non-zero if any file fails, so it doubles as a CI / pre-commit gate.
"""

import glob
import sys

import yaml

SKILL_REQUIRED = ("name", "description", "license")


def split_frontmatter(text):
    """Return the YAML frontmatter block, or None if the file has none."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1]


def main():
    errors = []
    targets = sorted(glob.glob("skills/*/SKILL.md") + glob.glob("commands/*.md"))

    for path in targets:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()

        fm = split_frontmatter(text)
        if fm is None:
            errors.append(f"{path}: missing YAML frontmatter (--- block)")
            continue

        try:
            data = yaml.safe_load(fm)
        except yaml.YAMLError as exc:
            first = str(exc).splitlines()[0]
            errors.append(f"{path}: invalid YAML — {first}")
            continue

        if not isinstance(data, dict):
            errors.append(f"{path}: frontmatter is not a mapping")
            continue

        if path.startswith("skills/"):
            missing = [k for k in SKILL_REQUIRED if k not in data]
            if missing:
                errors.append(f"{path}: missing required key(s): {', '.join(missing)}")

    if errors:
        print(f"Frontmatter check failed ({len(errors)} issue(s)):\n", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"Frontmatter OK — {len(targets)} file(s) validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
