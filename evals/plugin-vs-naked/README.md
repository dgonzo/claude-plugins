# Writing plugin compared with a bare Claude Code session

The writing plugin cuts linter findings by 83 percent. It drops from 3.4 to 0.6 findings per 100 words. Replies get 20 percent shorter and the first sentence halves in length. Tables and diagrams show up far more often. The cost is four times the dollars per run, because the plugin session loads skills before answering. Nothing is blocked.

## Test design

```
 7 prompts ──▶ 2 arms ──▶ 2 runs each ──▶ 28 replies + 4 files
                                              │
                                              ▼
                                   writing linter + counts
```

| Arm | How it runs | What it loads |
|---|---|---|
| Plugin | `claude -p` in a fresh temp folder | Global CLAUDE.md, writing plugin 1.0.0, other installed plugins |
| Naked | `claude -p --safe-mode` in a fresh temp folder | Nothing user-configured |

A smoke test confirmed the split. The naked arm saw no `writing:` skill. The plugin arm saw `writing:writing-standard`.

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

| Measure | Plugin | Naked |
|---|---|---|
| Linter findings per 100 words | 0.6 | 3.4 |
| Linter findings in total | 26 | 179 |
| Mean words per output | 261 | 327 |
| Mean words in first sentence | 11.9 | 21.2 |
| Outputs with a table | 12 of 16 | 2 of 16 |
| Outputs with a diagram | 6 of 16 | 3 of 16 |
| Design docs with Mermaid | 2 of 2 | 0 of 2 |
| Cost for 14 runs | $4.61 | $1.17 |
| Mean turns per run | 5.8 | 1.4 |
| Median seconds per run | 16.4 | 15.1 |

## Findings by rule

| Rule | Plugin | Naked |
|---|---|---|
| Long sentence | 2 | 43 |
| Comma stack | 6 | 43 |
| Bold as seasoning | 5 | 28 |
| Bold used as a heading | 1 | 13 |
| Slash as a conjunction | 0 | 12 |
| Filler word | 3 | 14 |
| Colon stack | 2 | 9 |
| Full sentence in a table cell | 4 | 0 |

## Findings per prompt

| Prompt | Plugin findings | Naked findings |
|---|---|---|
| p1-explain | 3 | 38 |
| p2-debug | 6 | 31 |
| p3-decision | 9 | 42 |
| p4-status | 6 | 19 |
| p5-designdoc | 0 | 32 |
| p6-pr | 0 | 15 |
| p7-rewrite | 2 | 2 |

## What the naked arm did not show

The bare model avoided several failures the plugin targets. It used no em-dashes and no praise openers. It ended no reply with a menu. It put the recommendation first in p3 and the blocker first in p4. It paired ticket IDs with plain names in p4.

The gap is in sentence shape and format choice. Naked replies run long sentences with stacked commas. They lean on bold and bullets where the plugin uses tables and diagrams. The naked design docs had tables but no request-flow diagram.

## Linter false positives

The linter overcounts in two places.

1. The em-dash rule fires on en-dash ranges such as "3–4 levels". All 7 naked em-dash findings are ranges. The naked outputs contain no em-dash.
2. The hard-wrap rule fires on an email sign-off such as "Thanks," then a name. All 3 hard-wrap findings in p4 are sign-offs.

Both are worth a linter fix. Neither changes the result.

## Limits of this test

- The plugin arm also loads superpowers and nine other plugins. Some of the extra cost and turns come from them.
- Two runs per prompt is a small sample.
- The linter is the plugin's own instrument. It measures the surface rules the plugin teaches. It cannot score a buried point. The first-sentence length is a rough proxy for that.
- The plugin arm tried a web search in p3 and was denied. In an interactive session it would add sources and cost.

## Files

- [prompts/](prompts/) contains the seven prompts.
- [runs/plugin/](runs/plugin/) and [runs/naked/](runs/naked/) contain each reply as `.md`, raw CLI output as `.json` and design docs as `.file.md`.
- [results.csv](results.csv) has one row per output. [aggregate.json](aggregate.json) has the arm totals.
- [run_one.sh](run_one.sh) runs one arm, prompt and repeat. [jobs.txt](jobs.txt) lists all 28.
- [score.py](score.py) rescores every output.

To rerun, from this folder:

```
xargs -P 7 -L 1 ./run_one.sh < jobs.txt
python3 score.py
```
