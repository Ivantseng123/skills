# AGENTS.md

## Global Constraints

- The whole repo is a single Claude Code plugin named `skills`. The plugin manifest is `.claude-plugin/plugin.json` at the repo root; `.claude-plugin/marketplace.json` exposes it as the lone plugin (`source: "./"`).
- Each skill lives at `skills/<skill>/{SKILL.md, README.md}` and is auto-discovered from the root `skills/` directory. Slash commands (if any) live in root `commands/`, hooks in root `hooks/hooks.json`.
- If you add, remove, or rename anything under `skills/`, `commands/`, or `hooks/`, update the root `README.md` and bump the `version` in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` in the same change.
- Every `SKILL.md` frontmatter must include `name`, `description`, and `license`. The single plugin version lives in `.claude-plugin/{plugin,marketplace}.json`, not in `SKILL.md`.
- `SKILL.md` carries the runtime rules the agent must follow; the per-skill `README.md` carries the human-facing overview and rationale. Don't duplicate one into the other.
- Hook commands reference skill-bundled scripts via `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/...` — the plugin root is the repo root.
- Avoid `_`-prefixed subdirectories; use `.`-prefixed names for hidden helpers.
- Skill evals go in an `evals/` directory next to that skill's `SKILL.md` (e.g., `skills/<skill>/evals/`).
- `scripts/check-frontmatter.py` validates frontmatter and is the CI gate (`.github/workflows/validate-skills.yml`). Run it before pushing.
