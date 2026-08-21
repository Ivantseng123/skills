# Skills

Ivan's collection of agent skills.

## Available Skills

- **[webapp-manual](skills/webapp-manual/)** — Build a web system's operation manual (操作說明書 / 操作手冊 / user guide) as a `.docx` from scratch — enumerating the nav bar into a table of contents — or maintain an existing one, kept true to the running app: verify pages against the live SPA (the sign-in method is read from source, not assumed), capture and annotate screenshots, and edit the OOXML directly — sections, field-spec tables, and the Table of Contents. Needs browser automation for capture — a Playwright MCP, or Node + the `playwright` package.
- **[uncertainty-manifest](skills/uncertainty-manifest/)** — Force an agent's hidden assumptions onto the page before it touches production code: a structured 4-section Manifest (Assumptions with data-lineage and cardinality sub-sections, Unknowns, Cross-source conflicts, Domain terms), every claim tagged `VERIFIED` / `CITED` / `INFERRED` / `GUESS` so the downstream review spends its budget where the uncertainty actually is.
- **[cross-review](skills/cross-review/)** — Hand a spec, plan, or PR to a fresh-eyes sub-agent that never saw your reasoning and let it try to knock the work down. Anchored mode walks an Uncertainty Manifest line by line; open mode derives one from the artifact. Spec and plan reviews are advisory; pre-push PR reviews run a three-lens panel and block on Criticals — and a Critical that can't name a concrete failure scenario is auto-demoted.

`uncertainty-manifest` and `cross-review` pair into a contract-and-court review workflow — the combined manual-invocation guide, including what each Confidence tag makes the reviewer do, is [docs/manifest-cross-review-workflow.md](docs/manifest-cross-review-workflow.md) (Traditional Chinese).

## Installation

### Claude Code Plugin

Everything ships as a single plugin — install once and all skills above are available:

```bash
/plugin marketplace add Ivantseng123/skills
/plugin install skills@ivantseng123-skills
```

### Codex Plugin

Codex has the same marketplace flow (the Codex App, or a recent codex CLI — the `codex plugin add` install step isn't in older CLI builds, which only register the marketplace):

```bash
codex plugin marketplace add Ivantseng123/skills
codex plugin add skills@ivantseng123-skills
```

Restart Codex (or open a new thread) after installing.

### OpenCode, Cursor, Copilot & other agents

The cross-agent [`skills`](https://skills.sh) CLI installs the SKILL.md skills into whichever agent you target — it reads this public repo directly, no marketplace registration needed:

```bash
npx skills add Ivantseng123/skills -a opencode   # OpenCode
npx skills add Ivantseng123/skills -a cursor     # Cursor (or -a windsurf, -a cline, …)
npx skills add Ivantseng123/skills -g            # every detected agent, globally
```

OpenCode discovers skills in `~/.agents/skills/`, `~/.claude/skills/`, and `~/.config/opencode/skills/` (plus project-local `.opencode/skills/`, `.claude/skills/`, `.agents/skills/`) — so a skill already installed for Claude Code or Codex shows up in OpenCode automatically.

`npx skills add --help` lists the supported agents (70+).

## License

MIT
