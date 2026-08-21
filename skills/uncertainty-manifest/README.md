# uncertainty-manifest

Force an agent's hidden assumptions onto the page — as a structured, confidence-tagged **Uncertainty Manifest** — before it touches production code.

## The problem it solves

An LLM has no epistemic "I don't know" state. Generation doesn't slow down at the points where the model is guessing; nothing in the output marks a guess as a guess. So the instruction everyone writes — *"ask when you're not sure"* — fails silently, because the model never notices it isn't sure.

The workaround is to invert the requirement. Instead of waiting for the model to *feel* uncertain, make it produce a document that exposes its assumptions to someone else's scrutiny. That document is the Manifest.

## What it produces

One markdown file per task, at `<project-root>/.claude/manifest/<task-slug>.md`, in four mandatory sections (plus two sub-sections that turn out to catch the most expensive bugs):

- **§1 Assumptions** — one line each, with a `Source` (`file:line`, doc section, the user's own words, or an honest `none`) and a **Confidence tag**: `VERIFIED` / `CITED` / `INFERRED` / `GUESS`. Reading the code caps at `CITED`; `VERIFIED` means you executed something that exercises the claim itself.
- **§1a Data Lineage** — for every field the change reads or writes: which table or entity is the *source of truth*, who writes it, who reads it, and — the part that does the work — which **same-named fields on other tables were not used, and why**. Grep finds every table exposing a name; it never tells you which one is the truth.
- **§1b Cardinality** — for every cross-entity reference: 1:1 / 1:N / N:M, the evidence, and whether a human confirmed it. Cardinality is a business fact, not a schema fact. `findOneBy*` might just mean "pick first of many."
- **§2 Unknowns** — each with a *closed-form* question (yes/no or multiple choice) and a `Blocking` flag. Open-ended questions invite the agent to re-assume the answer.
- **§3 Cross-source conflicts** — at least three checkpoints actually searched. "No conflict" is a valid finding, but only after the grep.
- **§4 Domain terms** — each linked to a glossary or flagged `NEW_TERM`, which means *stop and ask*, never *infer from context*.

The Confidence tags aren't decoration. They're what lets the downstream review concentrate its budget where the uncertainty actually is, instead of sweeping every line uniformly.

## When to invoke it

The trigger is **"the plan has crystallised into specific edits"** — specific files, specific methods, specific schema changes — not "a formal planning command was run."

- At the end of a planning phase, in whatever form your workflow has one.
- Before any change touching more than ~3 files or crossing module boundaries.
- Before any business-logic change in a regulated domain (insurance, finance, healthcare, legal).
- **Especially for lightweight tasks that skip planning entirely** — "幫我修這個 bug", "add an X". These look like they bypass planning, but the plan is happening silently on the way to the first edit. That's where the agent assumes the most and writes the least down.

It does **not** trigger at spec stage. While the discussion is still "approach A or approach B", there are no file paths to anchor on — keep it a discussion, and come back once it converges.

## Nothing enforces this

The skill ships as text. No process refuses to run, nothing gates the first edit, and nothing checks that your four sections say anything real. The skill states the discipline explicitly — existence, completeness, freshness, scope match, no side-door writes — so the honest failure is at least a visible one. A Manifest is worth exactly what you were willing to write into it truthfully.

What it does cost, so nobody is surprised: the skill writes one markdown file per task under `<project-root>/.claude/manifest/` inside your own repo, and the paired `cross-review` at PR tier spawns up to three sub-agents in parallel — three reviews' worth of tokens per run, not one.

## Pairs with cross-review

The Manifest is the *contract*; [`cross-review`](../cross-review/) is the *court*. Writing the Manifest is not the last step of planning — the last step is handing it to a fresh-eyes sub-agent that walks §1–§4 line by line and tries to knock each claim down. Without that, the Manifest is a self-satisfied checklist nobody challenged.

The combined manual workflow — when to write, when to review, and what the review does with each Confidence tag — is documented in [`docs/manifest-cross-review-workflow.md`](../../docs/manifest-cross-review-workflow.md) (Traditional Chinese).

See [`SKILL.md`](SKILL.md) for the runtime rules, the full section templates, and a worked example.

## Installation

```bash
npx skills add Ivantseng123/skills --skill uncertainty-manifest -a codex   # Codex (or -a cursor, …)
npx skills add Ivantseng123/skills --skill uncertainty-manifest -g         # every detected agent
```

In Claude Code you can also: `/plugin marketplace add Ivantseng123/skills`

## License

MIT
