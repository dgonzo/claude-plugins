# Changelog

## 2.0.1

- The repo is now `dgonzo/dgonzo-plugins`. The old name redirects. The install ID stays `writing@dgonzo`.
- Listings show "Writing" by David Gonzalez. The manifests also set a category and tags.
- One-command install for Claude Code. INSTALL.md covers Cowork, team repos and release files.
- Rule 10 bans "holds" and "carries" as vague verbs. Write "contains" or "applies" instead. The plugin's own text no longer uses them.
- The plugin-vs-naked eval compares the plugin with a bare session. Linter findings fall from 3.4 to 0.9 per 100 words. Its summary is in the plugin README.

## 2.0.0

- One standard. The writing-standard skill is the single source, 14 rules. It gained the plain-word swap table and the say-it-once rule. Never hard-wrap is its own rule. Sentence caps and condition-before-command steps are in. New rule on names and numbers.
- working-style gains the recommendations rule. Recommend only when asked for a decision. Then give one with the evidence beside it. Never a menu.
- A fallback card ships with the plugin and a SessionStart hook loads it. The global instruction shrinks to two lines.
- A surface note for hosts that show Mermaid as text, such as the VS Code extension chat.
- New review-prose skill for diffs and PR descriptions. New `/writing:lint <file>` command.
- The linter prints the standard's rule number on every finding.
- Release packaging: `make release` builds a `.plugin` file for Cowork and a marketplace zip for Claude Code.

## 1.0.0

- First release. Three skills: writing-standard, working-style and improve-readability. The prose linter and the PostToolUse lint hook.
