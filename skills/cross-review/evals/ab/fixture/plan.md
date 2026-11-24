# Plan: cap-discount

1. In `src/discount.py`, cap `pct` at 50 inside `apply_discount`: any value above 50 is treated as 50.
2. Add `test_cap_above_fifty` to `tests/test_discount.py`: `apply_discount(100, 60)` returns `50.0`.
3. Run `python3 -m unittest` and keep it green.
