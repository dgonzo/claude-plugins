#!/usr/bin/env python3
"""Score every run with the writing linter plus structural counts. Writes results.csv and summary.md."""
import collections, csv, json, re, subprocess, sys
from pathlib import Path

E = Path(__file__).resolve().parent
LINT = E.parents[1] / "plugins/writing/scripts/writing_lint.py"
OPENERS = re.compile(r"^(great|good|excellent) (question|catch|point)|^you'?re (absolutely )?right|^sure[,!]|^certainly", re.I)
OFFER = re.compile(r"(want me to|would you like|let me know|happy to|shall i|should i)\b", re.I)


def lint(path):
    out = subprocess.run([sys.executable, str(LINT), "--json", str(path)], capture_output=True, text=True).stdout
    return json.loads(out).get(str(path), []) if out.strip() else []


def first_sentence(text):
    body = "\n".join(l for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#"))
    m = re.split(r"(?<=[.!?])\s", body.strip(), maxsplit=1)
    return m[0] if m else ""


def score(path, arm, prompt, rep, kind):
    text = path.read_text()
    findings = lint(path)
    words = len(re.findall(r"\b\w[\w'-]*\b", text))
    last = [l for l in text.strip().splitlines() if l.strip()][-1] if text.strip() else ""
    row = {
        "arm": arm, "prompt": prompt, "rep": rep, "kind": kind, "words": words,
        "findings": len(findings), "per100w": round(100 * len(findings) / max(words, 1), 1),
        "first_sentence_words": len(first_sentence(text).split()),
        "em_dash": text.count("—"), "semicolon": len(re.findall(r";(?=\s)", text)),
        "mermaid": text.count("```mermaid"), "tables": len(re.findall(r"^\|[ :-]+\|", text, re.M)),
        "box_drawing": int(bool(re.search(r"[─-╿]", text))),
        "praise_opener": int(bool(OPENERS.search(text.strip()))),
        "ends_offer": int(bool(OFFER.search(last) or last.rstrip().endswith("?"))),
    }
    row["by_rule"] = dict(collections.Counter(f["rule"] for f in findings))
    return row


rows = []
for arm in ("plugin", "naked"):
    for p in sorted((E / "runs" / arm).glob("*-r[0-9].md")):
        prompt, rep = p.stem.rsplit("-r", 1)
        rows.append(score(p, arm, prompt, rep, "reply"))
    for p in sorted((E / "runs" / arm).glob("*.file.md")):
        prompt, rep = p.name.replace(".file.md", "").rsplit("-r", 1)
        rows.append(score(p, arm, prompt, rep, "file"))

cols = [k for k in rows[0] if k != "by_rule"] + ["by_rule"]
with open(E / "results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({**r, "by_rule": json.dumps(r["by_rule"])})

# Aggregate per arm.
agg = {}
for arm in ("plugin", "naked"):
    rs = [r for r in rows if r["arm"] == arm]
    n = len(rs)
    rules = collections.Counter()
    for r in rs:
        rules.update(r["by_rule"])
    agg[arm] = {
        "outputs": n,
        "words_mean": round(sum(r["words"] for r in rs) / n),
        "findings_total": sum(r["findings"] for r in rs),
        "findings_per100w": round(100 * sum(r["findings"] for r in rs) / sum(r["words"] for r in rs), 1),
        "first_sentence_words_mean": round(sum(r["first_sentence_words"] for r in rs) / n, 1),
        "em_dash_total": sum(r["em_dash"] for r in rs),
        "semicolon_total": sum(r["semicolon"] for r in rs),
        "outputs_with_diagram": sum(1 for r in rs if r["mermaid"] or r["box_drawing"]),
        "outputs_with_table": sum(1 for r in rs if r["tables"]),
        "praise_openers": sum(r["praise_opener"] for r in rs),
        "ends_with_offer_or_question": sum(r["ends_offer"] for r in rs),
        "rules": rules,
    }
json.dump(agg, open(E / "aggregate.json", "w"), indent=2, default=dict)
print(json.dumps(agg, indent=2, default=dict))
