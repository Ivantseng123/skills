# AGENTS.md

## Global Constraints

- The whole repo is a single plugin named `skills`, installable from two marketplaces. **Claude Code**: `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` (`source: "./"`). **Codex**: `.codex-plugin/plugin.json` (declares `skills: "./skills"`), exposed by `.agents/plugins/marketplace.json` whose plugin `source.path` `./plugins/skills` is a symlink back to the repo root (`plugins/skills -> ..`). So `codex plugin marketplace add` works alongside `/plugin marketplace add`.
- Each skill lives at `skills/<skill>/{SKILL.md, README.md}` and is auto-discovered from the root `skills/` directory. Slash commands (if any) live in root `commands/`, hooks in root `hooks/hooks.json`.
- If you add, remove, or rename anything under `skills/`, `commands/`, or `hooks/`, update the root `README.md` and bump the `version` in **all** version-carrying manifests in the same change: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, and `package.json`.
- Every `SKILL.md` frontmatter must include `name`, `description`, and `license`. The plugin version lives in the manifests (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `package.json`), not in `SKILL.md`.
- `SKILL.md` carries the runtime rules the agent must follow; the per-skill `README.md` carries the human-facing overview and rationale. Don't duplicate one into the other.
- Hook commands reference skill-bundled scripts via `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/...` — the plugin root is the repo root.
- Avoid `_`-prefixed subdirectories; use `.`-prefixed names for hidden helpers.
- Skill evals go in an `evals/` directory next to that skill's `SKILL.md` (e.g., `skills/<skill>/evals/`).
- `scripts/check-frontmatter.py` validates frontmatter and is the CI gate (`.github/workflows/validate-skills.yml`). Run it before pushing.
