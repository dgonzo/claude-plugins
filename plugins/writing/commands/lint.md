---
description: Run the writing linter on one file and print its output
argument-hint: <file>
allowed-tools: Bash(python3:*)
---

Linter output for `$ARGUMENTS`:

!`if [ -n "$ARGUMENTS" ]; then python3 "${CLAUDE_PLUGIN_ROOT}/scripts/writing_lint.py" $ARGUMENTS; else echo "Usage: /writing:lint <file>"; fi`

Reply with the output above, verbatim. Add nothing before it and nothing after it. Do not fix anything.
