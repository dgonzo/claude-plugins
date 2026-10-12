---
name: improve-readability
description: Review one Markdown, Quarto or text file for readability against the writing-standard skill. Use for "improve readability", "is this readable", "check the writing", "lint the prose", "this doc is hard to follow", or a file path after /writing:improve-readability. Reports findings and proposed rewrites. Never edits the file.
---

# improve-readability

Review one file against the `writing-standard` skill. Return findings and proposed rewrites. Do not edit the file.

## Steps

1. Load the `writing-standard` skill. If the repo has `WRITING.md`, read it too.
2. Run the linter and keep its output:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/writing_lint.py" <path>
```

3. Read the file as a reader with no context. Check what the linter cannot: is the first sentence the point, does each heading parse cold, does any paragraph want to be a table or diagram, is anything said twice, does any sentence break the register rule.
4. Report in this order: the one biggest defect, then a table of findings with line, rule and proposed rewrite, then the linter findings you judged false. Four columns maximum.
5. Offer the rewrite of the whole file only if asked.

Leave thousands-separator commas and slashes inside paths alone. Those are the only linter findings to ignore without comment.
