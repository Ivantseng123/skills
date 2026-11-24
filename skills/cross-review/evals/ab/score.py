"""Score one A/B run directory. usage: score.py <run dir> <A|B>"""
import json, pathlib, re, subprocess, sys

d, scen = pathlib.Path(sys.argv[1]), sys.argv[2]
final = (d / ".final.txt").read_text(errors="replace") if (d / ".final.txt").exists() else ""
reviews = sorted((d / "docs/manifest/reviews").rglob("*.md")) if (d / "docs/manifest/reviews").exists() else []

def cjk_ratio(text):
    """Share of prose lines that contain Chinese; headings, indented lines, code and quotes are left out."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    lines = [re.sub(r"`[^`]*`|「[^」]*」|\"[^\"]*\"", "", l).strip() for l in text.splitlines()
             if not re.match(r"\s*#|    ", l)]
    lines = [l for l in lines if re.search(r"[A-Za-z\u4e00-\u9fff]{4}", l)]
    return round(sum(bool(re.search(r"[\u4e00-\u9fff]", l)) for l in lines) / max(len(lines), 1), 2)

rc = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "src/*.py"], cwd=d).returncode
if rc not in (0, 1):
    sys.exit(f"git diff failed with exit {rc} in {d}")
src_changed = rc == 1
tests = subprocess.run(["python3", "-m", "unittest", "-q"], cwd=d, capture_output=True, text=True)
other = subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True, text=True).stdout.split("\n")
stray = [l[3:] for l in other if l and not re.match(r"(src/|tests/|docs/manifest/reviews/|docs/manifest/cap-discount\.md|\.final|\.std|\.run|\.score)", l[3:])]
manifest_changed = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "docs/manifest/cap-discount.md"], cwd=d).returncode != 0

score = {
    "findings_visible": bool(re.search(r"(🔴|🟡|🟢)\s*\**\s*(Critical|Major|Minor)|^\|\s*(🔴|🟡|—)\s*\|", final, re.M)),
    "report_saved": bool(reviews),
    "report_path_named": any(r.name in final for r in reviews),
    "guess_raised": None if scen == "A" else bool(re.search(r"外部|呼叫|caller|depend", final, re.I) and (re.search(r"[?？]", final) or re.search(r"(Requires user adjudication|Your call)[:：]\s*(?!none|nothing)\S", final, re.I))),
    "decision": "carried_on" if src_changed else "stopped",
    "decision_right": src_changed == (scen == "A"),
    "tests_green": tests.returncode == 0,
    "cjk_ratio_final": cjk_ratio(final),
    "cjk_ratio_report": cjk_ratio(reviews[-1].read_text()) if reviews else None,
    "review_files": [str(r.relative_to(d)) for r in reviews],
    "manifest_changed": manifest_changed,
    "stray_files": stray,
    "final_lines": final.count("\n"),
}
print(json.dumps(score, ensure_ascii=False))
