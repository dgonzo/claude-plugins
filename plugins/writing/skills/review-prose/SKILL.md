---
name: review-prose
description: Review the prose in a diff, a PR description or a set of changed Markdown files against the writing-standard skill. Use for "review the prose", "check the writing in this diff" or "review the PR description". Also for /writing:review-prose with no argument, a git ref or a PR number. Reports findings and proposed rewrites. Never edits.
---

# review-prose

Review changed prose against the `writing-standard` skill. Same shape as `improve-readability`, over a diff instead of one file. Do not edit any file.

## What the argument selects

| Argument | Reviews |
|---|---|
| none | `git diff` of the working tree, prose files only |
| a ref | `git diff <ref>`, prose files only |
| a PR number | the PR body and its changed prose files, through `gh` |

Prose files are Markdown and plain text, including Quarto and MDX. Skip code and data files.

## Steps

1. Load the `writing-standard` skill. If the repo has `WRITING.md`, read it too.
2. Collect the text to review:
   - no argument: `git diff --name-only` filtered to prose files. Then `git diff -- <files>`
   - a ref: `git diff <ref> --name-only` filtered to prose files. Then `git diff <ref> -- <files>`
   - a PR number: `gh pr diff <n> --name-only` filtered to prose files. Then `gh pr diff <n>` and read only the hunks of those files
3. Run the linter and keep its output. For the no-argument and ref forms, lint the changed prose files in the working tree:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/writing_lint.py" <files>
```

   For a PR, the working tree may hold another version of each file. Lint the PR's own text through stdin instead. The body first, then each changed prose file at the PR head:

```
gh pr view <n> --json body -q .body | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/writing_lint.py"
git fetch -q origin "$(gh pr view <n> --json headRefName -q .headRefName)"
git show FETCH_HEAD:<file> | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/writing_lint.py"
```

4. Review the added and changed lines only. Read them as a reader with no context. Check what the linter cannot:
   - is the first sentence the point, in the PR body and in each changed section
   - does each new heading parse cold
   - does any new paragraph want to be a table or diagram
   - is anything said twice
   - does every ID and person carry a plain name on first use
   - does any sentence break the register rule
5. Report in this order:
   - one sentence on the biggest defect
   - a four-column findings table of file and line, then rule and proposed rewrite
   - structural suggestions, one per line
   - the linter findings you judged false
6. Offer the rewrite of a file or the PR body only if asked.

A structural suggestion names a paragraph that wants to be a table. Or a section that should move, or a buried point.

If nothing changed in a prose file, say so in one sentence and stop.

Leave thousands-separator commas, slashes inside paths and quoted examples of banned text alone. Those are the only linter findings to ignore without comment.
