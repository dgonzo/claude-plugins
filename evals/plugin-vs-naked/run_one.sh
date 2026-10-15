#!/bin/bash
# Usage: run_one.sh ARM PROMPT_ID REP. ARM is plugin, naked, plugin-only or raw.
# raw replaces the Claude Code system prompt with one neutral line, to measure the model without Claude Code's own style guidance.
# plugin-only needs PLUGIN_DIR set to the plugin folder. It skips user settings, so no other plugin and no global CLAUDE.md loads.
set -u
E="$(cd "$(dirname "$0")" && pwd)"
arm=$1; p=$2; rep=$3
out="$E/runs/$arm/$p-r$rep"
work=$(mktemp -d /tmp/pvn.XXXXXX)
flags=(-p --output-format json --permission-mode bypassPermissions --no-session-persistence)
[ "$arm" = naked ] && flags+=(--safe-mode)
[ "$arm" = raw ] && flags+=(--safe-mode --system-prompt "You are a helpful assistant. You can read and write files in the current directory.")
[ "$arm" = plugin-only ] && flags+=(--setting-sources project --plugin-dir "$PLUGIN_DIR")
[ -d "$E/fixtures/$p" ] && cp -R "$E/fixtures/$p/." "$work/"
cd "$work"
env -u CLAUDECODE -u CLAUDE_CODE_CHILD_SESSION -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_ENTRYPOINT claude "${flags[@]}" < "$E/prompts/$p.txt" > "$out.json" 2> "$out.err"
python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["result"])' "$out.json" > "$out.md" 2>>"$out.err"
[ -f "$work/design.md" ] && cp "$work/design.md" "$out.file.md"
rm -rf "$work"
echo "done $arm $p r$rep"
