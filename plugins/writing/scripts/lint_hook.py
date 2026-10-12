#!/usr/bin/env python3
"""PostToolUse hook. After a Write or Edit to a prose file, lint it and hand the findings back as context.
Exit 0 always. Never blocks, never edits."""
import json, os, re, subprocess, sys

PROSE = (".md", ".qmd", ".mdx", ".txt")
try:
    event = json.load(sys.stdin)
except Exception:
    sys.exit(0)
path = (event.get("tool_input") or {}).get("file_path") or ""
if not path.lower().endswith(PROSE) or not os.path.isfile(path):
    sys.exit(0)
if "/node_modules/" in path or "/.git/" in path:
    sys.exit(0)
lint = os.path.join(os.path.dirname(os.path.abspath(__file__)), "writing_lint.py")
out = subprocess.run([sys.executable, lint, path], capture_output=True, text=True).stdout.strip()
lines = [l for l in out.splitlines() if re.match(r".+:\d+: [a-z-]+: ", l)]
if not lines:
    sys.exit(0)
shown = lines[:25]
more = f"\n... {len(lines) - 25} more" if len(lines) > 25 else ""
noun = "finding" if len(lines) == 1 else "findings"
msg = (f"writing-standard linter on {os.path.basename(path)}: {len(lines)} {noun}. Fix each real one before you finish. "
       "Leave only thousands-separator commas, slashes inside paths, and quoted examples of banned text.\n"
       + "\n".join(shown) + more)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))
