## Uncertainty Manifest

### §1 Assumptions
- [ ] `apply_discount` is defined once, in `src/discount.py`.
  - Source: `src/discount.py:1`
  - Quote: `def apply_discount(price, pct):`
  - Confidence: CITED
- [ ] The cap is 50.
  - Source: `docs/pricing-rules.md:5`
  - Quote: "Discounts are capped at 50%."
  - Confidence: CITED
- [ ] No caller outside this repo passes a pct above 50 and depends on the uncapped result.
  - Source: none
  - Confidence: GUESS
- [ ] The existing test passes before the change.
  - Source: `tests/test_discount.py:7`
  - Confidence: INFERRED

### §2 Unknowns
- [ ] Should the cap later move to a config file?
  - Clarifying Q: move the cap to config in a later task (yes/no)?
  - Blocking: no
- [ ] Should the changelog mention the cap?
  - Clarifying Q: add a changelog line (yes/no)?
  - Blocking: no
- [ ] Does any caller outside this repo depend on discounts above 50%?
  - Clarifying Q: external callers rely on pct > 50 (yes/no)?
  - Blocking: yes
- [ ] Is the cap configurable?
  - Clarifying Q: hard-coded 50 (a) or a parameter (b)?
  - Blocking: no

### §3 Cross-source conflicts
- [ ] Callers of apply_discount — grep `apply_discount` in src/ and tests/ — only tests/test_discount.py
  - Resolution: no conflict
- [ ] Rounding — `src/discount.py:2` uses round(); plan.md says nothing about rounding
  - Resolution: keep round()
- [ ] Docs — `docs/pricing-rules.md:5` says capped at 50%; plan.md step 1 says cap at 50
  - Resolution: no conflict

### §4 Domain terms
- [ ] pct → `docs/pricing-rules.md:4`
- [ ] cap → `docs/pricing-rules.md:5`
- [ ] price → `docs/pricing-rules.md:3`
