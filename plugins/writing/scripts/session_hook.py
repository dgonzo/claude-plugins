#!/usr/bin/env python3
"""SessionStart hook. Prints standard/card.md as additionalContext so the rules hold before any skill loads.
Appends a surface note when the host cannot render Mermaid inline. Exit 0 always. Prints nothing if the card is missing."""
import json, os, sys

# CLAUDE_CODE_ENTRYPOINT value, then the note for a host that shows Mermaid and images as text.
SURFACE_NOTES = {
    "claude-vscode": "Surface note: this chat renders Mermaid fences and images as plain text. Draw a diagram as Unicode box-drawing inside a plain code fence, or use a table. Write Mermaid only into a Markdown file the reader opens in preview.",
}

card = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "standard", "card.md")
try:
    with open(card, encoding="utf-8") as fh:
        text = fh.read().strip()
except Exception:
    sys.exit(0)
if not text:
    sys.exit(0)
note = SURFACE_NOTES.get(os.environ.get("CLAUDE_CODE_ENTRYPOINT", ""))
if note:
    text += "\n\n" + note
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
