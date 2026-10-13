# Point a repo at the writing plugin

Each repo stops carrying its own writing rules and points at the `writing` plugin instead. One PR per repo. The plugin is the single source. A repo keeps only its project-only rules, in a `WRITING.md` at its root. Run this after the plugin's release PR has merged, so the install link below is live.

```
┌──────────────────┐  loads into  ┌───────────────────┐  overrides  ┌────────────────┐
│  writing plugin  │ ───────────▶ │  every session    │ ◀────────── │  WRITING.md    │
│  on the machine  │              │  in the target    │             │  in the target │
└──────────────────┘              └───────────────────┘             └────────────────┘
```

## Steps for one repo

1. Install the plugin on your machine. Follow [INSTALL.md](../INSTALL.md). Verify with "what is the writing rule on bold".
2. Find every file that carries writing rules:

```
grep -rl -i -E 'writing standard|writing\.md|writing_lint' --include='*.md' --include='Makefile' --include='*.yml' .
```

3. Replace the body of the repo's writing section with this line. Keep the heading. Delete everything else under it: the scope paragraph, the rule list and the check command.

```markdown
Prose follows the `writing` plugin. Install: see its [INSTALL.md](https://github.com/dgonzo/claude-plugins/blob/main/INSTALL.md).
```

4. If the deleted list held a rule the plugin does not have, put it in `WRITING.md` at the repo root. Use the template below. If nothing is project-only, add no file.
5. If the repo has its own readability skill, delete it. The plugin ships `improve-readability` and `review-prose`. Point every caller of the deleted skill at `/writing:improve-readability`. Point every file that says "follow the writing standard in AGENTS.md" at the plugin instead.
6. If the repo vendors the standard as a file, keep the file. Add the sync target and the CI check below. If it does not, skip this step.
7. Run `/writing:lint` on every Markdown file the PR touches. Fix findings.
8. Open the PR. Its body opens with what changed and what the repo still owns.

## WRITING.md template

```markdown
# Writing overrides for this repo

Audience: <who reads the output of this repo>.
Terms: <project IDs and their plain names, or a link to a glossary>.
Added rules: <one per line, or none>.
Relaxed rules: <one per line, or none>.
Project linter: <command, or none>.
```

## Vendored copies: sync target and drift check

A repo that vendors `standards/writing.md` or `scripts/writing_lint.py` keeps them so its own tooling works offline. The copies must match the plugin.

`make sync-writing` copies from the installed plugin and records its version in `standards/writing.version`. The standard is the skill file without its front matter. The install path comes from Claude Code's own registry, so an orphaned cache folder is never picked.

```makefile
WRITING_PLUGIN := $(shell python3 -c 'import json,os; d=json.load(open(os.path.expanduser("~/.claude/plugins/installed_plugins.json"))); print(d["plugins"]["writing@dgonzo"][0]["installPath"])' 2>/dev/null)

sync-writing: ## Copy the writing standard and linter from the installed writing plugin
	@test -n "$(WRITING_PLUGIN)" || { echo "writing plugin is not installed. See its INSTALL.md"; exit 1; }
	awk 'f==2{print} /^---$$/{f++}' "$(WRITING_PLUGIN)/skills/writing-standard/SKILL.md" | sed '1{/^$$/d;}' > standards/writing.md
	cp "$(WRITING_PLUGIN)/scripts/writing_lint.py" scripts/writing_lint.py
	python3 -c 'import json; print(json.load(open("$(WRITING_PLUGIN)/.claude-plugin/plugin.json"))["version"])' > standards/writing.version
```

Add `sync-writing` to `.PHONY`.

The CI check reads `standards/writing.version`. It fetches the same two files from the plugin's release tag for that version and fails on any difference. The installed plugin and the tag are the same files, so the two checks agree. The plugin repo is public, so no token is needed. Add the job under `jobs:` in the repo's validate workflow, indented to match its siblings.

```yaml
  writing-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Compare the vendored standard and linter with the plugin release
        run: |
          version=$(cat standards/writing.version)
          base="https://raw.githubusercontent.com/dgonzo/claude-plugins/v$version/plugins/writing"
          curl -fsSL "$base/skills/writing-standard/SKILL.md" | awk 'f==2{print} /^---$/{f++}' | sed '1{/^$/d;}' | diff - standards/writing.md
          curl -fsSL "$base/scripts/writing_lint.py" | diff - scripts/writing_lint.py
```

## Worked example: data-org

| File | Change |
|---|---|
| `AGENTS.md`, section "Writing standard" | the one-line body, delete the rest |
| `standards/writing.md` | keep, refresh with `make sync-writing` |
| `standards/writing.version` | new, written by `make sync-writing` |
| `scripts/writing_lint.py` | keep, refresh with `make sync-writing` |
| `Makefile` | add `sync-writing`, keep `lint-writing` |
| `.github/workflows/validate.yml` | add the `writing-drift` job |
| `plugins/data-org/skills/improve-readability/` | delete, the plugin's skill replaces it |
| `plugins/data-org/README.md` | point the readability lines at `/writing:improve-readability` |
| `plugins/data-org/.claude-plugin/plugin.json` | drop improve-readability from the description |
| `plugins/data-org-cowork-plugin/skills/draft-drd/SKILL.md` | "follow the writing standard in AGENTS.md" becomes "follow the writing plugin" |
| `plugins/data-org-cowork-plugin/skills/draft-dadr/SKILL.md` | same change |
| `WRITING.md` | new, with the repo's ID and name pairs |

The bullet "Pair every ID with its plain name on first use" is Rule 11 in the plugin. It does not go in `WRITING.md`. The repo's IDs and their plain names do.

## Acceptance per repo

- The repo has one writing section and its body is the one line from step 3.
- The step 2 grep lists only the vendored copies and the files that carry the pointer. The Makefile and the CI workflow count as pointers.
- `make sync-writing` leaves the tree unchanged on a repo that is in sync.
- A fresh session in the repo answers "what is the writing rule on bold" from the plugin.
