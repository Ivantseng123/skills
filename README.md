# Skills

Ivan's collection of agent skills.

## Available Skills

- **[webapp-manual](skills/webapp-manual/)** — Build a web system's operation manual (操作說明書 / 操作手冊 / user guide) as a `.docx` from scratch — enumerating the nav bar into a table of contents — or maintain an existing one, kept true to the running app: verify pages against the live SPA (the sign-in method is read from source, not assumed), capture and annotate screenshots, and edit the OOXML directly — sections, field-spec tables, and the Table of Contents. Needs browser automation for capture — a Playwright MCP, or Node + the `playwright` package.

## Installation

### Claude Code Plugin

Everything ships as a single plugin — install once and all skills above are available:

```bash
/plugin marketplace add Ivantseng123/skills
/plugin install skills@ivantseng123-skills
```

### Skills CLI

```bash
npx skills add Ivantseng123/skills -g
```

## License

MIT
