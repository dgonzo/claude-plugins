#!/usr/bin/env python3
"""SessionStart hook. Prints standard/card.md as additionalContext so the rules hold before any skill loads.
Exit 0 always. Prints nothing if the card is missing."""
import json, os, sys

card = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "standard", "card.md")
try:
    with open(card, encoding="utf-8") as fh:
        text = fh.read().strip()
except Exception:
    sys.exit(0)
if not text:
    sys.exit(0)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
