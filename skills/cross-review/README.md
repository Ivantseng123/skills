# cross-review

Hand a spec, plan, or pull request to a **fresh-eyes sub-agent** that has never seen your reasoning — and let it try to knock the work down.

## The problem it solves

A session that writes a plan develops tunnel vision. It walks its own reasoning to the end, and by the time it's done, the path it took looks like the only path there was. Whatever it glossed over on the way stays glossed over, because nothing in the context points at it.

A second session, kept deliberately ignorant of that reasoning, doesn't share the path. It reads the artifact cold, goes and looks at the code, and finds the source that was deprecated two commits ago.

Two limits are worth naming, because misunderstanding them turns this into theater:

- **Same model, same blind spots.** Two sessions on the same model share a training distribution. This catches *missed-it-from-context* failures, not *the model doesn't know this domain* failures — the latter needs the `NEW_TERM` mechanism in [`uncertainty-manifest`](../uncertainty-manifest/) plus a human.
- **Fresh eyes require isolation.** Show the reviewer your reasoning and it inherits your bias, then confirms it back to you. The prompt template withholds the original conversation on purpose.

## Two modes

- **Anchored** — an Uncertainty Manifest exists for this work. The reviewer walks §1–§4 line by line, re-verifying each cited source and challenging each assumption. Highest ROI: the author already did the work of naming the hidden state; the reviewer only has to test it.
- **Open** — no Manifest (an ad-hoc PR, legacy code, a third-party patch, or you skipped the step). The reviewer *derives* an implicit Manifest from the artifact in a first pass, then challenges it in a second. Still useful, but the reviewer pays the inference cost and may miss what an explicit Manifest would have surfaced.

## Three tiers

| Command | When | Policy |
|---|---|---|
| `cross-review spec` | After a spec is drafted | advisory |
| `cross-review plan` | After a Manifest is written or updated | advisory — but every Critical is answered item by item |
| `cross-review pr` | Before `git push` / `gh pr create` | blocking on Critical |

S-class changes (≤2 files, ≤20 lines, no business logic) skip the plan tier; the pre-push tier applies regardless.

## What it produces

A report in a fixed shape: a per-item verdict on every Manifest line (✅ Verified / ⚠️ Stale / ❌ Wrong / 🆕 Missing / ⏭️ Skipped, each cited to `file:line` except skipped items), hidden conflicts the reviewer found on its own, a three-scenario pre-mortem, and severity-sorted findings.

Two mechanics keep the report honest. **Confidence-tier dispatch**: `GUESS` and `INFERRED` claims get individually attacked, `CITED` claims get spot-checked, `VERIFIED` claims get skipped — the verification budget goes where the uncertainty is. **Falsifiable Criticals**: a 🔴 Critical that can't name a concrete failure scenario (specific input or state → specific wrong outcome) is auto-demoted to 🟡 Major, which is what stops the hallucinated-critical → fix → re-run → new hallucination loop.

For PRs the reviewer is a **panel of three parallel lenses** — correctness, secrets-and-scope, and domain — each given the same diff and a different mandate. Same-model reviewers share blind spots; you compensate with lens diversity, not with more reviewers.

## The failure mode it's guarding against

The tempting shortcut, every time this triggers, is: *I'll just grep it myself and write the review inline — cheaper than spawning an agent.* That kills the entire mechanism. A same-context review is worse than no review, because the user now believes an independent check happened. If your environment genuinely can't spawn an isolated sub-agent, the skill says to report the skip out loud rather than produce a review-shaped object.

The same honesty applies to the blocking tier: nothing mechanically stops `git push`. "Blocking" is a rule you keep, and the friction is the point.

## Pairs with uncertainty-manifest

The Manifest is the contract, cross-review is the court. See [`docs/manifest-cross-review-workflow.md`](../../docs/manifest-cross-review-workflow.md) for the combined manual workflow (Traditional Chinese), and [`SKILL.md`](SKILL.md) for the runtime procedure and the full sub-agent prompt template.

## Installation

```bash
npx skills add Ivantseng123/skills --skill cross-review -a codex   # Codex (or -a cursor, …)
npx skills add Ivantseng123/skills --skill cross-review -g         # every detected agent
```

In Claude Code you can also: `/plugin marketplace add Ivantseng123/skills`

## License

MIT
