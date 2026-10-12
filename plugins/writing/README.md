# writing

The house writing standard and working style, as one plugin for every surface. Project tweaks live in a `WRITING.md` at the repo root.

## The tiers

```mermaid
flowchart TD
  A[Tier 1: this plugin] -->|loads in| B[Chat]
  A -->|loads in| C[Cowork]
  A -->|loads in| D[Claude Code]
  E[Tier 2: global instructions] -->|tells each surface to load| A
  F[Tier 3: WRITING.md in the repo] -->|overrides| A
```

| Tier | Where it lives | What it holds |
|---|---|---|
| 1 plugin | this repo, installed from claude.ai | the full rules, the linter, the hook |
| 2 global instruction | Cowork settings, chat preferences, `~/.claude/CLAUDE.md` | twelve lines that say load the plugin and the rules that must hold before it loads |
| 3 project | `WRITING.md` at the repo root | audience, project terms, a rule added or relaxed, a project linter |

## What the plugin contains

| Component | Name | Job |
|---|---|---|
| Skill | `writing-standard` | the prose rules and the check before you send |
| Skill | `working-style` | session behaviour: answer first, no narration, do the work, hold the objective |
| Skill | `improve-readability` | review one file, report findings, never edit |
| Script | `scripts/writing_lint.py` | the mechanical rules, exit 0 always |
| Hook | PostToolUse on Write and Edit | lints every Markdown file an agent writes and feeds findings back |

The hook runs in Claude Code and in Cowork sessions on your computer. Chat has no hooks, so chat relies on the skill alone.

## Tier 2: the global instruction

Paste this block into Cowork global instructions, into claude.ai preferences, and keep it in `~/.claude/CLAUDE.md`. It is the fallback for the moment before the skill loads.

```markdown
Load the writing:working-style and writing:writing-standard skills before the first reply in every session and follow them. If a WRITING.md exists in the working folder, read it too.

Until they load: the point goes first. One idea per sentence, twenty words. Plain words. No em-dash asides, semicolons or "and/or". Diagram, then table, then prose. Never hard-wrap Markdown. Open every reply with the finding, then what is blocked and who owns it. Do not narrate, do not recap, do not add a recommendation nobody asked for. Review documents go in the repo as Markdown, never as an HTML artifact.
```

## Tier 3: WRITING.md

A plain Markdown file at the repo root. The skills read it before writing and it wins on conflict. Keep it short. A template:

```markdown
# Writing overrides for this repo

Audience: <who reads the output of this repo>.
Terms: <project IDs and their plain names, or a link to a glossary>.
Added rules: <one per line, or none>.
Relaxed rules: <one per line, or none>.
Project linter: <command, or none>.
```

## Updating the rules

Edit the skills here, bump `version` in `.claude-plugin/plugin.json`, commit and push. Every surface picks up the new version on its next sync. Run the linter on the skill files before you push.
