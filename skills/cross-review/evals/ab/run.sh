#!/usr/bin/env bash
# usage: run.sh <host: claude|codex|codex-ro> <scenario: A|B> <label> <SKILL.md path> <out root>
set -eu
host=$1 scen=$2 label=$3 skill=$4 out=$5
: "${out:?out root is required}"
here=$(cd "$(dirname "$0")" && pwd)
d="$out/$label-$host-$scen"
rm -rf "$d"; mkdir -p "$d"
cp -R "$here/fixture/." "$d/"
cp "$here/scenarios/$scen-manifest.md" "$d/docs/manifest/cap-discount.md"
mkdir -p "$d/skill"; cp "$skill" "$d/skill/SKILL.md"
( cd "$d" && git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm fixture )
set +e
prompt='請照 skill/SKILL.md 這份 cross-review 規則（只用這份，不要用其他版本），對 plan.md 跑 cross-review plan，Manifest 在 docs/manifest/cap-discount.md。審查結束後，依照規則決定要繼續實作 plan.md 還是停下來等我。'
start=$(date +%s)
case $host in
  claude) ( cd "$d" && claude -p "$prompt" --permission-mode bypassPermissions --output-format text >"$d/.final.txt" 2>"$d/.stderr.txt" ) ;;
  codex)  codex exec --sandbox workspace-write -C "$d" -o "$d/.final.txt" "$prompt" >"$d/.stdout.txt" 2>"$d/.stderr.txt" ;;
  codex-ro) codex exec --sandbox read-only -C "$d" -o "$d/.final.txt" "$prompt" >"$d/.stdout.txt" 2>"$d/.stderr.txt" ;;
  *) echo "unknown host: $host" >&2; exit 2 ;;
esac
echo "exit=$? secs=$(( $(date +%s) - start ))" >"$d/.run.txt"
python3 "$here/score.py" "$d" "$scen" >"$d/.score.json"
cat "$d/.score.json"
