# Skills

Ivan's collection of agent skills.

## Available Skills

- **[webapp-manual](skills/webapp-manual/)** — Build and maintain a web system's operation manual (操作說明書 / 操作手冊 / user guide) as a `.docx`, kept true to the running app: verify pages against the live SPA (JWT-into-`localStorage`, no Playwright MCP needed), capture and annotate screenshots, and edit the OOXML directly — sections, field-spec tables, and the Table of Contents.

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
