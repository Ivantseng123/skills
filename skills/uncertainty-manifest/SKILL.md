---
name: uncertainty-manifest
description: >-
  Force-surface hidden agent assumptions as a structured 4-section Manifest
  (Assumptions / Unknowns / Cross-source conflicts / Domain terms) before any
  non-trivial implementation. Its target is the plan's code-change structure —
  which files, methods, schema — so it triggers after the plan phase, not at spec
  stage. Use proactively at the end of planning, before cross-module or multi-file
  changes, before business-logic changes — and critically for lightweight tasks
  that skip planning (bug fixes, quick patches, "幫我修這個"), where the agent
  silently assumes the most. Especially important in regulated domains (insurance,
  finance, healthcare, legal). Pairs with the cross-review skill. Triggers on
  finishing a plan, post-plan implementation, cross-module changes, business-logic
  changes, bug fixes, quick patches, 幫我加, 幫我改, 幫我修, 改 A 錯 B, regression,
  "I assume", 規劃完成, 不確定, 商業邏輯變更. Does NOT trigger on spec drafting —
  the artifact is still diverging on design, not pinned to specific files/methods.
license: MIT
---

# Uncertainty Manifest

## Why this skill exists

LLMs don't have an epistemic "I don't know" state. Token generation doesn't slow down at uncertain points — there is no internal signal that says "this is a guess." So an instruction like "ask when you're not sure" silently fails: the model has no mechanism for *noticing* that it doesn't know.

The only reliable workaround is to invert the requirement. Instead of expecting the model to feel uncertain, require it to produce a structured output that exposes its assumptions to external scrutiny. That output is the **Uncertainty Manifest**.

A Manifest forces four kinds of hidden state into the open:

- Assumptions the agent is making about requirements or behavior
- Things the agent doesn't know but is about to act on
- Conflicts between sources (code vs. docs vs. tribal knowledge) the agent may have papered over
- Domain terms the agent may be using without grounding

With these four on a page, a human — or a reviewing agent via the `cross-review` skill — has a concrete object to challenge. Without them, the agent's reasoning is invisible until the broken code shows up.

## When to produce a Manifest

Produce one whenever the next step would touch production code with a *concrete change set* — meaning the files, methods, and schema mutations are already pinned down. The Manifest anchors on that change set, so it can't usefully exist before the change set does.

- At the end of the **plan** phase (or the equivalent moment in lightweight tasks — see below). This covers the output of whatever planning flow you use, a plan-mode exit, agent-self-produced numbered/bulleted step lists *with concrete file edits*, or lightweight implicit plans that materialize without a formal phase. The trigger is "the plan has crystallised into specific edits" — not "a specific skill was invoked".
- Before any change touching more than ~3 files or crossing module boundaries
- Before any business-logic change in regulated domains (insurance, finance, healthcare, legal)
- Anytime the agent is about to make an authoritative claim without a citable source

**Explicitly NOT triggered by the spec phase.** At spec stage the artifact is still diverging on *what to build* — the Manifest can't anchor on file paths or method signatures because none are pinned yet. Spec-stage uncertainty (design tradeoffs, scope questions, divergent options) belongs in ordinary design discussion with the user. The Manifest comes after spec → plan, when the discussion has converged onto a concrete change list.

If no Manifest exists yet and the change is post-plan / lightweight-with-implicit-plan, defer implementation. Implementation without a Manifest means acting on hidden assumptions — exactly the failure mode this skill prevents.

## Lightweight tasks without an explicit plan

The most common real-world scenario isn't "user runs a formal planning command to crystallise the change set." It's "user types: '幫我修這個 bug' or '加個 X 功能'" — straight to implementation, no formal planning phase. **Treat this as the rule, not the exception.**

This workflow looks like it bypasses planning, but planning is happening — silently, inside the agent's head, on the way to the first Write/Edit/MultiEdit/NotebookEdit. The implicit plan crystallises the moment the agent decides "I'll edit file X, change method Y to Z." *That moment* is when the Manifest matters — not earlier (no concrete change set yet) and not later (code already half-written).

When this skill activates for a lightweight task:

1. **Reconstruct the implicit plan first.** Outline to yourself what you're about to do — which files you'll touch, what logic you'll change, what you're assuming about existing behavior. This doesn't need to be shown to the user as a "plan document," but it has to exist before the Manifest gets filled in, because the Manifest *captures* that plan's hidden state.
2. **Write the Manifest as if a plan had been written.** §1 Assumptions captures the implicit plan's hidden state. §1a / §1b / §3 / §4 apply the same way — the formality of the upstream phase doesn't change what needs to be surfaced.
3. **Don't shortcut to a 3-line "this is small" Manifest.** A 5-line bug fix can still touch a §1 assumption that turns out wrong — that's exactly the "改 A 錯 B" failure mode in regulated domains. The Manifest's value scales with the surprise-density of the change, not with line count or task description length.

Note on what *doesn't* count as an implicit plan: if the user is still discussing options ("should we use approach A or B?"), the implicit plan hasn't crystallised — that's design-stage discussion, keep it a discussion. Only once the change set has converged ("ok, edit file X to add method Y") does Manifest territory begin.

If the user genuinely just wants a 1-line typo fix and the change is verifiably non-semantic, **say so to the user and let them waive the Manifest** — the exemption is theirs to grant, never yours to grant yourself. Name the change, state why you believe it is non-semantic, and wait for the answer. Nothing machine-checks this exemption, which is exactly why it's the one that quietly widens; the point of routing it through the user is that "this is small" might itself be the assumption the Manifest would have caught.

## Sizing the change (S / M / L)

Judge the class yourself before writing the Manifest. Nothing classifies the change for you, and nothing corrects a wrong call — a change misfiled as S skips a review it needed.

- **S** — ≤2 files, ≤20 lines, no business logic. Still write all four §-sections with ≥3 substantive lines each, and §3 still needs ≥3 checkpoints you actually ran. May skip the plan-tier `cross-review` trigger described below; the pre-push `cross-review pr` tier applies unchanged.
- **M** — 3–10 files, **or any business-logic / cross-module change** regardless of size. Full Manifest plus a `cross-review plan` run (advisory, but every Critical is handled item by item — see below).
- **L** — >10 files, schema changes, or cross-system changes. Same as M, plus batched implementation with each batch independently verified.

**Business logic** means code affecting amount / rate / allocation calculations, state transitions, or externally visible behavior. **Can't tell which class it is → treat it as M.** The classes exist to allocate review effort, not to earn exemptions; when the sizing argument starts feeling clever, you're arguing yourself out of a review you need.

## What this skill doesn't cover

The Manifest's §3 cross-source check is bounded by what `grep` and `Read` can see — typically the current repository or working tree. A few categories of risk fall outside that boundary:

- **Cross-microservice contract drift.** If a change touches an API that the current repo consumes but the producer lives in a separate service, §3 won't catch a schema mismatch. The Manifest can flag that a contract is involved (note it in §1 with `Source: none — touches cross-service contract` and `Confidence: GUESS`, copying it to §2 per the §1 rule), but verifying alignment needs a schema registry, integration tests, or the producer's repo open in a parallel session.
- **Cross-repo monorepo blast radius.** Same problem, larger scope. A rename in a shared lib used by eight services is invisible to a single-repo grep.
- **Runtime / infrastructure changes.** The Manifest handles code-level assumptions well; less so for "this Helm value change affects pod CPU limits which affects timeouts which affects retries..." That's infra-engineering.
- **Domain knowledge the model doesn't have.** If the agent literally doesn't know a domain term, §4's `NEW_TERM` flag halts and asks the user — but the agent cannot validate domain semantics on its own. A project-level glossary plus human review fills this gap.

When the change crosses any of these boundaries, the Manifest is **necessary but not sufficient**. Surface the boundary in §1 explicitly so cross-review and the user know to apply external checks (integration tests, contract validation, domain expert review).

## Where the answer lives

Two workflow questions come up often enough to be worth pointing at directly. Both have a defined answer — neither is left to the agent to improvise:

- **PR-time stale Manifest** — At `git push` / `gh pr create` the Manifest may not have been touched since before the diff took its final shape. The behavior is defined: re-read it, re-validate each assumption against the diff that is actually shipping, update it in place, and only then run `cross-review pr`. Don't push under a stale anchor and don't review against one. Stated as a rule in "Manual discipline" § Freshness below, and enforced from the other side by `cross-review` § "Step 1 — Pick the mode", which requires the same freshness check before an anchored review and says to drop to open mode deliberately — and out loud — if you choose not to refresh.

- **Scope-creep re-trigger criteria** — Defined in `cross-review` § "When to invoke" (plan-tier re-trigger rule); that section is authoritative and this bullet is a pointer. Summary: Manifest updates made in direct response to a review report do not re-trigger the plan tier; updates adding ≥2 new `GUESS` items or ≥1 new `Blocking: yes` Unknown do; max 2 automatic plan-tier re-runs, then ask the user.

## Manifest structure

Always produce all four sections. **§1, §2, §3 and §4 each carry at least 3 non-empty content lines** — a section with genuinely nothing to report still gets explicit lines stating what was checked and came up empty (e.g. three `- checked <place> — none found` entries). "Empty" only counts as information after the agent has actually looked, and the looking must be written down.

§1a and §1b are conditional, and the 3-line floor does not apply to them. §1a is required whenever the change reads or writes a data field; §1b whenever it depends on a cross-entity reference. When one genuinely doesn't apply, write the heading with a single explicit line — `N/A — <one-line reason>`, e.g. `N/A — this change touches no data fields, only log formatting` — rather than padding it to three lines of filler. A false `N/A` is a lie you tell the reviewer; padding is a lie you tell yourself.

### §1 Assumptions

For each assumption the agent is making:

```markdown
- [ ] <one-sentence statement of the assumption>
  - Source: `<file:line | doc:section | conv:turn-N | none>`
  - Confidence: VERIFIED | CITED | INFERRED | GUESS
```

The source field is what makes this section useful. Without it, an assumption is a guess wearing a tie. If no source can be cited honestly, write `Source: none`, mark `Confidence: GUESS`, and copy the entry into §2 Unknowns. `GUESS` isn't shameful — it's accurate, and it routes the item to the user for resolution before code gets written.

**Confidence tags** (mandatory, one per §1 entry — downstream review dispatches on this):

| Tag | Meaning | Downstream treatment (cross-review) |
|---|---|---|
| `VERIFIED` | Confirmed by something actually EXECUTED this session (ran a test / query / command and observed the result) | Skipped unless contradicted by another finding |
| `CITED` | Concrete source cited (file:line / official doc / user's own words) but not executed | Spot-check sample: ≥3 entries (all, if fewer) |
| `INFERRED` | Reasoned from reading code, naming, or convention; the claim itself has no direct citation | Per-item adversarial verification |
| `GUESS` | No honest source | Per-item adversarial verification + routed to user |

Tie-break rule: torn between two tags → pick the LOWER one. Reading code is `CITED` at best; `VERIFIED` requires execution evidence, and the thing executed must exercise THE CLAIM ITSELF (run the test that proves the behavior; run the query and see the claimed value) — grep/Read/ls only prove text exists, which caps at `CITED`. Reviewers treat untagged entries as `INFERRED`. The treatment column above is a convenience copy — the authoritative downstream treatments live in `cross-review` § "Confidence-tier dispatch".

### §1a Data Lineage (mandatory for every field / column the change reads or writes)

`grep <field-name>` finds *every* table that exposes that name. It does not tell you *which one* is the source of truth. The most expensive class of bug in regulated domains is "I read `exchangeRate` from the wrong table — it existed there too, just held a stale or default value." `§1` Assumptions doesn't catch this because the assumption "exchangeRate has the right value" reads plausible until you ask *where* it came from.

For every data field touched by the change, write one entry:

```markdown
- [ ] <field name, e.g. exchangeRate>
  - source_of_truth: `<table.column | entity.field | repository.method>`
  - populated_by: `<writer file:line | migration script | service method>`
  - consumed_by: `<reader file:line | report SQL | downstream service>`
  - alternative_sources_NOT_used: `<list same-named fields on other tables/entities>`
  - why_not_alternative: <one sentence reasoning>
```

Hard rule: if `source_of_truth` cannot be cited from real code/schema, the entry is `Blocking` and copies to §2. Schema is the most expensive thing to get wrong — it propagates through every consumer (writer, reader, SQL report, downstream API).

Domain trigger: in finance, insurance, billing, and order management, the same business concept (rate / amount / id) routinely appears on 3–5 tables with subtly different meanings (order-level vs. line-item-level vs. shipment-level vs. ledger-level). **Any field where ≥2 tables expose the same name is an automatic §1a entry** — no exceptions.

Anti-pattern to catch: writing `- [ ] allocationRate comes from PricingRule` in §1 with `Source: PricingRuleRepository.findById` — the source citation looks complete, but it's circular. The repository exists, the field exists, so the assumption is "verified" — except it never asked whether *another* table also has `allocation_rate` that's the actual truth. §1a forces that question by requiring `alternative_sources_NOT_used` to be enumerated.

### §1b Cardinality (mandatory for every cross-entity reference)

Cardinality (1:1 vs. 1:N vs. N:M) is *business knowledge*, not schema knowledge. A missing unique constraint doesn't mean 1:N — could be a data invariant enforced in service code. A `findOneBy*` method returning a single result doesn't mean 1:1 — could be "pick first of many." The agent cannot derive cardinality from grep alone; it must be confirmed.

For every cross-entity reference the change depends on:

```markdown
- [ ] <relationship, e.g. Order → Shipment>
  - cardinality: 1:1 | 1:N | N:M
  - evidence: `<FK definition | unique constraint | repo return type | API response sample | user-confirmed business fact>`
  - user_confirmed: yes | no | not_yet
  - implementation_depends_on_cardinality: yes | no
```

Hard rule: if `user_confirmed: not_yet` AND `implementation_depends_on_cardinality: yes`, the entry is `Blocking` and copies to §2 — surface the cardinality question to the user *before* writing code, not after the multi-shipment (or multi-X) reality comes back as a UAT bug report.

Signals to grep for (these are necessary clues, not sufficient evidence):

- `findAllBy*Ids(Set<Long>)` returning `List<X>` — likely 1:N, but the `List` could also be aggregation across multiple parents; ask the user
- `findOneBy*` / `findFirstBy*` / `Optional<X>` — ambiguous: 1:1 or "pick first of many"
- Method parameter `Set<Long>` / `Collection<Long>` — caller already assumes multiple, but this doesn't tell you whether one parent maps to multiple children

Cardinality should be confirmed by **business fact, not method signature**. A 5-line user question ("does one X ever have multiple Y in production?") replaces hours of UAT-driven redesign. The cheapest way to get this fact is to ask, in plain language, before implementation — not infer it from `List<>` return types.

Anti-pattern to catch: assuming 1:1 because the user-facing UI shows one record at a time. UI presentation ≠ data model. An order detail screen routinely shows one shipment in the active tab while three exist in the underlying table.

### §2 Unknowns

For each thing the agent doesn't know:

```markdown
- [ ] <what is unknown>
  - Clarifying Q: <closed-form question — yes/no or multiple choice>
  - Blocking: yes | no
```

Closed-form questions matter. An open-ended question ("how should we handle X?") invites the agent to re-assume the answer when the user replies. A discrete choice leaves the agent with nothing to fill in.

`Blocking: yes` items must be resolved before implementation. `Blocking: no` items can be deferred and revisited later.

### §3 Cross-source conflicts

List at least three checkpoints — places where two or more sources might disagree, and that the agent has actually checked:

```markdown
- [ ] <conflict topic>
  - Source A: `<where>` — <what it says>
  - Source B: `<where>` — <what it says>
  - Resolution: <which to follow | PENDING>
```

"No conflict found" is a valid resolution, but only after the search was performed. The three-checkpoint minimum is there to break the agent's instinct to skip this section. Cross-checking is what catches the silent drift between documentation, code, and tribal knowledge.

### §4 Domain terms

For every domain-specific term the spec or plan uses:

```markdown
- [ ] <term>
  - Glossary: `<ref/glossary.md#term | path>` | NEW_TERM
```

`NEW_TERM` means the term is not in any glossary the agent can find. In that case, stop and ask the user for a definition. Inferring the meaning from context is exactly the failure mode that produces plausible-but-wrong terminology in regulated-domain code.

## Self-check before exiting the plan phase

Run through this list. If any answer is "no," return to the relevant section before declaring the plan complete.

- Does every §1 assumption cite a real source, or is it explicitly marked `Confidence: GUESS`?
- Does every §1 entry carry a `Confidence` tag (`VERIFIED` / `CITED` / `INFERRED` / `GUESS`)? Untagged entries get treated as `INFERRED` downstream — tag them yourself, don't leave it to the reviewer's default.
- Does every field the change reads or writes have a §1a entry with `source_of_truth` cited, or is it `Blocking`? (especially: any field with a same name on ≥2 tables)
- Does every cross-entity reference the change depends on have a §1b entry with cardinality declared, evidence cited, and `user_confirmed` status? (any `not_yet` + implementation-depends becomes `Blocking`)
- Does every §2 Unknown have a closed-form clarifying question?
- Are there at least three §3 checkpoints, each based on an actual grep?
- Is every §4 term either linked to a glossary entry or marked `NEW_TERM`?

`GUESS` items and `Blocking: yes` Unknowns should be resolved with the user before implementation begins — otherwise the implementation is acting on the very assumptions this skill exists to surface.

§1a and §1b are the highest-ROI sections in regulated domains. Skipping them is exactly how the agent ends up redesigning the whole calculation path after a single user sentence ("oh, one order can have multiple shipments"). A 5-minute user fact-check on §1a/§1b beats N rounds of cross-review on a wrong-frame plan.

## Persisting the Manifest to a file

This skill owns the full lifecycle: deciding the slug, creating the file, writing the content, and updating it as planning progresses. The user shouldn't need to run any setup command — invoking this skill is the trigger.

Save the Manifest to:

```
<project-root>/.claude/manifest/<task-slug>.md
```

### Picking the slug

When this skill activates, derive a kebab-case slug from the task at hand — e.g., `fix-discount-rate`, `add-return-approval-flow`. Rules:

- Specific over generic. `update-billing` is fine; `update` or `feature-1` is not.
- Lowercase letters, digits, and dashes only. No spaces or special characters.
- 2–5 words is usually right.
- Pick it from the task description without pausing planning. Mention the chosen slug in your response so the user can push back if they want a different one — but don't block on confirmation.

### File handling

- If `<project-root>/.claude/manifest/<task-slug>.md` does not exist: `mkdir -p .claude/manifest`, then Write the file with the full 4-section Manifest content.
- If it exists: update it in place. The same task always maps to the same file — don't create a parallel copy with a slightly-different slug.
- Don't ask the user to run a helper command first. The skill is the helper.

### Frontmatter — `file_globs` scope binding (recommended)

Manifest files include YAML frontmatter for metadata. Declare `file_globs` to bind the Manifest to a specific scope: an explicit, written statement of which files this Manifest authorizes you to change. It turns the scope-match discipline below into something you can check at a glance instead of from memory, and it heads off the "stale-pairing" failure mode where a Manifest written for task A quietly gets reused to justify edits for task B.

```yaml
---
name: order-refund-allocation
file_globs:
  - "src/main/java/com/example/order/refund/**"
  - "src/main/java/com/example/order/pricing/**"
  - "deploy/staging/configmap.yaml"
  - "deploy/production/configmap.yaml"
description: ...
metadata:
  type: plan
---
```

Keep the glob syntax simple and literal — list paths individually rather than leaning on clever patterns:

- `path/to/dir/` — prefix match: any file under this directory
- `path/to/dir/**` — same as above (canonical form)
- `path/to/file.ext` — exact file match

If `file_globs` is absent, the Manifest's scope is whatever its §1 / §1a prose happens to describe — workable, but you'll be checking scope from memory every time. Declaring globs is strongly recommended for any Manifest covering more than one file, and near-mandatory when you're likely to switch tasks before the change ships.

### Manual discipline — nothing checks this for you

This skill is pure text: no tooling gates your edits, no process refuses to run. Every item below is a rule you keep, and the only thing standing between you and a silent violation is your own honesty about it.

1. **Existence** — before the first Write / Edit to production code, a Manifest covering this change set already exists on disk. No Manifest → don't edit; write it first.
2. **Completeness** — all four §-sections present, each carrying ≥3 substantive content lines. Nothing stops you from padding three filler lines; the padding only fools you, and it fools the reviewer downstream who trusts the section was filled in honestly.
3. **Freshness** — a Manifest written hours ago describes the codebase as it was then. The checkable proxy for "stale", since elapsed time isn't one: **the Manifest is stale once the working tree has changed in a way it didn't anticipate** — another author's commit lands, a pull/rebase rewrites files, or your own edits stray outside its declared scope. Your own planned, in-scope edits are what it anticipated; they don't invalidate it. So: before resuming implementation after an unanticipated change, and again before `git push`, re-read it and confirm each assumption still holds; update in place where it doesn't. Never run `cross-review pr` against a stale anchor — the review will faithfully verify claims nobody is making any more.
4. **Scope match** — the file you're about to edit falls inside the Manifest's declared `file_globs` (or, absent globs, inside its stated change set). Reusing task A's Manifest to authorize task B's edits is the exact failure this rule exists to prevent, and it is invisible from the inside.
5. **No side-door writes** — writing production code through `cat > file`, a heredoc redirect, or a scripted file write is the same edit with the discipline stripped off. Go through the normal edit path so the change is visible as a change.

If you catch yourself reasoning toward an exception to any of the five, say so to the user rather than granting it to yourself. The reasoning is usually right about the specific case and wrong about the habit.

## Trigger cross-review at the end

Writing the Manifest is **not** the last step of planning. Immediately after the Manifest file is written or updated, invoke the `cross-review` skill in `plan` mode. This is part of this skill's workflow, not optional — with two carve-outs:

- **S-class exemption**: if the Manifest belongs to an S-class change (≤2 files, ≤20 lines, non-business-logic — see "Sizing the change" above; unsure of the class → treat as M and run the review), skip this plan-tier trigger. The pre-push `cross-review pr` tier still applies unchanged.
- **No re-trigger loop**: Manifest updates made in direct response to a cross-review report do NOT re-trigger the plan tier — the re-trigger rule is defined in `cross-review` § "When to invoke" (authoritative).

- **Why** — The Manifest captures the agent's *own* model of the world. Cross-review is what tests that model against the codebase with fresh eyes. Without it, the Manifest is a self-satisfied checklist that nobody challenges.
- **How** — Spawn a sub-agent with the artifact (the plan/spec content) plus the Manifest file. See the `cross-review` skill for the exact prompt template and procedure; this skill just triggers it.
- **Tier** — At plan stage the review is **advisory** — present the report, let the user decide what to act on, do not block implementation on it. (PR stage is different — that one blocks on critical.)
- **Don't ask first** — Don't prompt the user "should I run cross-review?" That's ceremony and predictable bikeshedding. Run it, present the report, then let the user respond.

If the cross-review surfaces items that need user input or change the plan, update the Manifest file in place to reflect the new understanding before implementation begins.

### Plan-stage critical findings — mandatory acknowledgement

The advisory tier for plan-stage means the *workflow* doesn't block, but the *agent* must still acknowledge every 🔴 Critical finding. Silent dismissal of a critical finding is exactly the failure mode this clause exists to prevent.

If the plan-stage cross-review report contains any 🔴 Critical item, before any production-code Write / Edit / MultiEdit / NotebookEdit:

1. **Update the Manifest** to incorporate or refute the critical finding — don't silently ignore.
2. **Report each critical finding back to the user** with your decision (absorb / pushback / defer) and rationale.
3. **Wait** for user response before proceeding to implementation.

"This is just advisory" is not a license to drop a critical finding on the floor. Advisory means the workflow doesn't gate; it does not mean the agent ignores.

## Example — order refund allocation

A realistic Manifest for a task like "add automatic refund allocation across order line items in the return flow":

```markdown
## Uncertainty Manifest

### §1 Assumptions
- [ ] Auto-allocation handles full-order refunds only, not partial line-item returns.
  - Source: `conv:turn-3` (user confirmed "full-order first")
  - Confidence: CITED
- [ ] Orders in scope are single-tax-class carts; mixed-tax carts stay on the legacy
      manual-refund path and are not touched by this change.
  - Source: `docs/refund-scope.md §1.4`
  - Confidence: CITED
- [ ] Allocation rate is read from `PricingService.findActiveRule()`.
  - Source: `src/pricing/PricingService.java:142`
  - Confidence: CITED
- [ ] Loyalty-point reversal is out of scope for this change.
  - Source: none — not discussed; copied to §2
  - Confidence: GUESS

### §1a Data Lineage
- [ ] allocationRate
  - source_of_truth: `pricing_rule.allocation_rate`
  - populated_by: `PricingService.save` (admin pricing UI)
  - consumed_by: `RefundWorkflow.allocate:88`, loyalty-point reversal (if in scope)
  - alternative_sources_NOT_used: `order_line_item.allocation_rate` (per-line override, only for mixed-tax carts), `promotion_rule.allocation_rate` (promotion engine only)
  - why_not_alternative: the per-line override is only ever populated for mixed-tax carts, which §1 puts out of scope; `promotion_rule.allocation_rate` is written and read exclusively by the promotion engine, which this refund flow never calls
- [ ] refundAmount (read at allocation)
  - source_of_truth: `order_return_event.gross_amount`
  - populated_by: `ReturnEventService.recordReturn`
  - consumed_by: `RefundWorkflow.allocate:91`
  - alternative_sources_NOT_used: `order_return_event.net_amount` (post-restocking-fee, different semantic)
  - why_not_alternative: allocation is gross-of-fee per business rule (conv:turn-5)

### §1b Cardinality
- [ ] ReturnEvent → PricingRule (active at return date)
  - cardinality: 1:N
  - evidence: `PricingService.findActiveRule()` returns `List<PricingRule>` — a single return can match several stacked rules (the singular method name over a collection is exactly the intent-vs-cardinality trap §1b exists to catch)
  - user_confirmed: not_yet
  - implementation_depends_on_cardinality: yes (must iterate all matching rules, not pick first)
- [ ] Order → LineItem
  - cardinality: 1:N
  - evidence: `order_line_item.order_id` FK + no unique constraint
  - user_confirmed: not_yet
  - implementation_depends_on_cardinality: yes (refund amount must be split across line items per share)

### §2 Unknowns
- [ ] Does this change include synchronous loyalty-point reversal?
  - Clarifying Q: Include loyalty-point reversal in scope? (yes/no)
  - Blocking: yes
- [ ] Do gift-card and store-credit refunds share the allocation path?
  - Clarifying Q: gift-card/store-credit path is (a) shared (b) separate (c) out of scope?
  - Blocking: yes

### §3 Cross-source conflicts
- [ ] Allocation rate decimal precision
  - Source A: `src/pricing/PricingService.java:142` — BigDecimal scale=6
  - Source B: `docs/pricing-spec.md §3.2` — "four decimal places"
  - Resolution: PENDING
- [ ] Allocation trigger timing
  - Source A: `RefundWorkflow.java:88` — at return approval
  - Source B: ops notes (conv:turn-7) — "nightly batch"
  - Resolution: PENDING
- [ ] Retry policy on allocation failure
  - Searched `Refund*.java` and `docs/error-handling.md` — not mentioned
  - Resolution: PENDING — needs user decision

### §4 Domain terms
- [ ] Restocking fee → `ref/glossary.md#restocking-fee`
- [ ] Store credit → `ref/glossary.md#store-credit`
- [ ] Chargeback → NEW_TERM ← stop, ask user
- [ ] MDR (Merchant Discount Rate) → NEW_TERM ← stop
```

## How this pairs with cross-review

The Manifest is the anchor that `cross-review` uses in its **anchored mode** — a reviewing sub-agent walks §1–§4 line by line, independently verifying each cited source, challenging each unknown, and looking for items §3 missed. This is the highest-ROI form of cross-review because the assumptions are already named on the page.

If a Manifest doesn't exist, `cross-review` falls back to **open mode** — the reviewer derives an implicit Manifest from the artifact during review, then challenges that. Still useful, but lower ROI than anchored because the reviewer pays the inference cost up front. Producing a real Manifest (this skill's job) is what upgrades the pair from open to anchored.

Together: the Manifest surfaces the agent's model of the world, and cross-review tests that model against the codebase — either with the explicit map the author wrote (anchored) or one the reviewer derives along the way (open).

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "This task is too small for a Manifest" | Then the Manifest is small — but "small" still means all 4 §-sections with ≥3 substantive lines each. No Manifest isn't an option. |
| "I'm confident in my assumptions" | Then citing the file:line is trivial. If it's trivial, do it. |
| "Nothing conflicts" | State that explicitly *after* the grep. Skipping §3 isn't the same as confirming no conflict. |
| "The domain term is obvious from context" | This is exactly how plausible-but-wrong terminology slips into regulated-domain code. |
| "I already cited a Source for `exchangeRate` in §1" | The §1 citation proves the field exists in *that* source, not that it's the source of truth. §1a forces you to enumerate the alternative same-named fields and explain why each is *not* the truth. |
| "The repo method is `findOneBy*` so it must be 1:1" | Method name is intent signal, not cardinality fact. `findOne` could return any one of many. §1b requires business-fact confirmation, not method-name inference. |
| "I'll discover cardinality during implementation if I'm wrong" | Yes, you'll discover it — at UAT, after committing 8 commits, after writing tests for the wrong shape. §1b is "the 5-minute version of that discovery, before code." |
| "Nothing is enforcing this, so it's a suggestion" | Nothing enforced it in the failures that motivated the skill either. The Manifest is worth exactly what you're willing to write into it honestly. |
