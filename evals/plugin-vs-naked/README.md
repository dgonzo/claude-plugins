# Writing plugin compared with a bare Claude Code session

The writing plugin cuts linter findings by about 75 percent. Loaded alone, it drops them from 3.4 to 0.9 per 100 words. Replies get 25 percent shorter and the first sentence is 40 percent shorter. Tables appear in 12 of 16 outputs against 2. The plugin alone costs 1.3 times a bare session. Nothing is blocked.

## Test design

```
 7 prompts ──▶ 3 arms ──▶ 2 runs each ──▶ 42 replies + 6 files
                                              │
                                              ▼
                                   writing linter + counts
```

| Arm | How it runs | What it loads |
|---|---|---|
| Plugin alone | `claude -p --setting-sources project --plugin-dir <plugin>` | Writing plugin 2.0.1, fetched from GitHub |
| Full setup | `claude -p` | Writing plugin 1.0.0, global CLAUDE.md, ten other plugins |
| Naked | `claude -p --safe-mode` | Nothing user-configured |

Every run starts in a fresh, empty temp folder. Smoke tests confirmed each arm. The naked arm saw no `writing:` skill. The plugin-alone arm saw the five `writing:` skills and the session card. It saw no other plugin and no CLAUDE.md.

Each prompt targets a failure the plugin was built for.

| Prompt | Task | Failure it targets |
|---|---|---|
| p1-explain | Explain database indexes | Long prose, no structure |
| p2-debug | Diagnose a failed deploy from a log | Buried cause |
| p3-decision | Pick a message queue | Option menu, fake balance |
| p4-status | Weekly status for a manager | Blocker last, bare ticket IDs |
| p5-designdoc | Write design.md to disk | Hard wrap, no diagram |
| p6-pr | PR description from a diff | Filler, passive voice |
| p7-rewrite | Tighten a wordy README paragraph | Filler, long words |

## Results by arm

| Measure | Plugin alone | Full setup | Naked |
|---|---|---|---|
| Linter findings per 100 words | 0.9 | 0.6 | 3.4 |
| Mean words per output | 241 | 261 | 327 |
| Mean words in first sentence | 12.6 | 11.9 | 21.2 |
| Outputs with a table | 12 of 16 | 12 of 16 | 2 of 16 |
| Outputs with a diagram | 6 of 16 | 6 of 16 | 3 of 16 |
| Design docs with Mermaid | 2 of 2 | 2 of 2 | 0 of 2 |
| Cost for 14 runs | $1.52 | $4.61 | $1.17 |
| Mean turns per run | 1.4 | 5.8 | 1.4 |
| Median seconds per run | 14.6 | 16.4 | 15.1 |

The full setup costs three times the plugin alone. Its extra turns load skills from the other plugins and from the CLAUDE.md instruction. The writing plugin adds little cost by itself.

## Findings by rule

| Rule | Plugin alone | Full setup | Naked |
|---|---|---|---|
| Long sentence | 4 | 2 | 43 |
| Comma stack | 2 | 6 | 43 |
| Bold as seasoning | 7 | 5 | 28 |
| Bold used as a heading | 4 | 1 | 13 |
| Slash as a conjunction | 1 | 0 | 12 |
| Filler word | 5 | 3 | 14 |
| Full sentence in a table cell | 8 | 4 | 0 |

## Findings per prompt

| Prompt | Plugin alone | Full setup | Naked |
|---|---|---|---|
| p1-explain | 4 | 3 | 38 |
| p2-debug | 7 | 6 | 31 |
| p3-decision | 9 | 9 | 42 |
| p4-status | 10 | 6 | 19 |
| p5-designdoc | 0 | 0 | 32 |
| p6-pr | 1 | 0 | 15 |
| p7-rewrite | 2 | 2 | 2 |

## What the naked arm did not show

The bare model avoided several failures the plugin targets. It used no em-dashes and no praise openers. It ended no reply with a menu. It put the recommendation first in p3 and the blocker first in p4. It paired ticket IDs with plain names in p4.

The gap is in sentence shape and format choice. Naked replies run long sentences with stacked commas. They lean on bold and bullets where the plugin arms use tables and diagrams. The naked design docs had tables but no request-flow diagram.

## The words "holds" and "carries"

Version 1.0.0 of the standard used "holds" and "carries" more than 20 times. Version 2.0.1 bans both in Rule 10.

| Arm | Plugin version | Uses in all outputs |
|---|---|---|
| Full setup | 1.0.0 | 12 |
| Naked | none | 5 |
| Plugin alone | 2.0.1 | 4 |

The model copies the verbs of the text it loads. The linter has no check for these words yet.

## Lint hook

In the plugin-alone arm, a session wrote a file with an em-dash aside and a semicolon. The PostToolUse hook reported both findings back to the session.

## Linter false positives

The linter overcounts in two places.

1. The em-dash rule fires on en-dash ranges such as "3–4 levels". All 7 naked em-dash findings are ranges. The naked outputs contain no em-dash.
2. The hard-wrap rule fires on an email sign-off such as "Thanks," then a name. Every hard-wrap finding in p4 is a sign-off.

Both are worth a linter fix. Neither changes the result.

## Limits of this test

- The full setup and the plugin-alone arm differ in plugin version as well as in what else loads.
- Two runs per prompt is a small sample.
- The linter is the plugin's own instrument. It measures the surface rules the plugin teaches. It cannot score a buried point. The first-sentence length is a rough proxy for that.
- The full-setup arm tried a web search in p3 and was denied. In an interactive session it would add sources and cost.

## Files

- [prompts/](prompts/) contains the seven prompts.
- [runs/](runs/) has one folder per arm. Each reply is a `.md` file. Raw CLI output is `.json`. Design docs are `.file.md`.
- [results.csv](results.csv) has one row per output. [aggregate.json](aggregate.json) has the arm totals.
- [run_one.sh](run_one.sh) runs one arm, prompt and repeat.
- [jobs.txt](jobs.txt) lists the full-setup and naked runs. [jobs-plugin-only.txt](jobs-plugin-only.txt) lists the plugin-alone runs.
- [score.py](score.py) rescores every output.

To rerun, from this folder:

```
xargs -P 7 -L 1 ./run_one.sh < jobs.txt
PLUGIN_DIR=<path to plugins/writing> xargs -P 7 -L 1 ./run_one.sh < jobs-plugin-only.txt
python3 score.py
```
