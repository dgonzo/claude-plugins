#!/bin/bash
# Usage: run_one.sh ARM PROMPT_ID REP. ARM is plugin, naked or plugin-only.
# plugin-only needs PLUGIN_DIR set to the plugin folder. It skips user settings, so no other plugin and no global CLAUDE.md loads.
set -u
E="$(cd "$(dirname "$0")" && pwd)"
arm=$1; p=$2; rep=$3
out="$E/runs/$arm/$p-r$rep"
work=$(mktemp -d /tmp/pvn.XXXXXX)
flags=(-p --output-format json --permission-mode acceptEdits --no-session-persistence)
[ "$arm" = naked ] && flags+=(--safe-mode)
[ "$arm" = plugin-only ] && flags+=(--setting-sources project --plugin-dir "$PLUGIN_DIR")
cd "$work"
claude "${flags[@]}" < "$E/prompts/$p.txt" > "$out.json" 2> "$out.err"
python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["result"])' "$out.json" > "$out.md" 2>>"$out.err"
[ -f "$work/design.md" ] && cp "$work/design.md" "$out.file.md"
rm -rf "$work"
echo "done $arm $p r$rep"
