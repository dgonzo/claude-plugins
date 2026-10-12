#!/usr/bin/env python3
"""Lint Markdown prose against the writing-standard skill. Reports findings, never edits.

Usage:
    python3 scripts/writing_lint.py FILE [FILE ...]
    python3 scripts/writing_lint.py --json FILE
    cat draft.md | python3 scripts/writing_lint.py

Each finding is one line: path:line: rule: Rule N. detail. N is the rule number in the
writing-standard skill (see STANDARD_RULE). Exit 0 always. The linter catches the
mechanical surface. It cannot catch a buried point or a cryptic heading, so a human
still reads the text.
"""
import json
import re
import sys

# Linter rule slug, then the rule number in the writing-standard skill it enforces.
STANDARD_RULE = {
    "heading-gloss": 5, "heading-long": 6, "heading-restated": 5,
    "table-wide": 7, "table-sentence": 7, "table-break": 7,
    "hard-wrap": 9,
    "em-dash": 3, "semicolon": 3, "and-or": 3, "slash": 3, "colon-stack": 3, "parenthetical": 3,
    "symbol": 6, "not-x-but-y": 5, "bold-seasoning": 5, "bold-heading": 5,
    "filler": 4, "marketing": 4, "pre-frame": 4, "praise-opener": 5,
    "long-word": 10, "phrasal-verb": 10, "nominalization": 10, "passive": 10, "rule-of-three": 5,
    "long-sentence": 2, "comma-stack": 2,
}

# Rule 4 in the standard. Words that carry no fact.
FILLER = [
    "genuinely", "deliberately", "exactly", "literally", "honestly", "truly", "actually",
    "simply", "just", "really", "very", "quite", "fairly", "somewhat", "essentially",
    "basically", "fundamentally", "arguably", "notably", "particularly", "incredibly",
    "remarkably", "crucial", "vital",
]
MARKETING = [
    "seamless", "seamlessly", "robust", "powerful", "comprehensive", "comprehensively",
    "cutting-edge", "effortless", "effortlessly", "world-class", "next-generation",
    "revolutionary", "blazing", "lightning-fast", "elegant", "delightful", "turnkey",
    "best-in-class", "state-of-the-art", "game-changing", "battle-tested",
    "enterprise-grade", "supercharge", "unlock", "unleash", "empower", "empowers",
]
PREFRAME = [
    "worth noting", "it's important to", "it is important to", "the real question",
    "critically", "importantly", "keep in mind", "at the end of the day", "here's the thing",
    "to be honest", "that said", "it should be noted", "please note that", "as mentioned",
    "as noted above", "stated honestly",
]
PRAISE = ["great question", "good catch", "you're absolutely right", "you are absolutely right", "excellent point"]
# Long word, then the short common word that replaces it.
LONG_WORDS = {
    "utilize": "use", "utilizes": "uses", "utilized": "used", "utilizing": "using", "utilization": "use",
    "leverage": "use", "leverages": "uses", "leveraged": "used", "leveraging": "using",
    "facilitate": "help", "facilitates": "helps",
    "ensure": "make sure", "ensures": "makes sure", "ensuring": "making sure",
    "prior to": "before", "subsequent to": "after",
    "regarding": "about", "concerning": "about",
    "obtain": "get", "obtains": "gets", "acquire": "get", "acquires": "gets",
    "demonstrate": "show", "demonstrates": "shows",
    "commence": "start", "commences": "starts", "initiate": "start", "initiates": "starts",
    "additionally": "also", "furthermore": "also", "moreover": "also",
    "in order to": "to", "a variety of": "several", "in the event that": "if",
    "due to the fact that": "because", "numerous": "many", "myriad": "many",
    "plethora": "many", "whilst": "while", "amongst": "among", "aforementioned": "that",
    "delve": "look", "delves": "looks",
}
PHRASAL = {
    "spin up": "start", "spin down": "stop", "spun up": "started", "reach out": "contact",
    "reaching out": "contacting", "dive into": "read", "dives into": "reads",
    "diving into": "reading", "kick off": "start", "kicks off": "starts",
    "roll out": "release", "rolls out": "releases", "tear down": "remove",
    "ramp up": "increase", "circle back": "return", "drill down": "look closer",
}
NOMINAL = re.compile(
    r"\b(?:perform(?:s|ed)?|conduct(?:s|ed)?|carry out|carries out|make use of|makes use of)\s+"
    r"(?:an?|the)?\s*\w+(?:tion|ment|ance|ence|sis|ysis)\b", re.I)
BE = r"(?:am|is|are|was|were|be|been|being)"
PP_IRREG = r"(?:done|made|sent|read|built|kept|held|set|put|run|written|shown|given|taken|found|seen|known|thrown|drawn|chosen|left)"
PASSIVE = re.compile(rf"\b{BE}\s+(?:\w+ed|{PP_IRREG})\s+by\b", re.I)
SYMBOLS = {"→": "becomes", "⇒": "becomes", "←": "comes from", "∪": "or", "∩": "and", "≠": "is not", "≈": "about"}

SENTENCE_MAX = 20  # words. Rule 2 allows 25 for descriptive prose. 20 is the flag.
COMMA_MAX = 1


def word_count(s):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-/]*", s))


def split_sentences(s):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", s)
    return [p.strip() for p in parts if p.strip()]


def find_phrases(text, phrases):
    low = text.lower()
    for ph in phrases:
        if re.search(r"(?<![a-z])" + re.escape(ph) + r"(?![a-z])", low):
            yield ph


def lint_lines(lines):
    """Yield (lineno, rule, detail). lineno is 1-based."""
    in_code = False
    fence = None
    in_front = False
    prev_prose = False  # previous line was a prose line (hard-wrap detection)
    prev_heading = None
    bold_in_section = 0
    section_line = 1
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        stripped = line.strip()

        if i == 1 and stripped == "---":
            in_front = True
            continue
        if in_front:
            if stripped == "---":
                in_front = False
            continue

        m = re.match(r"^(\s*)(`{3,}|~{3,})", line)
        if m:
            if not in_code:
                in_code, fence = True, m.group(2)[0]
            elif line.strip().startswith(fence):
                in_code, fence = False, None
            prev_prose = False
            continue
        if in_code:
            continue

        if not stripped:
            prev_prose = False
            continue

        is_heading = stripped.startswith("#")
        is_list = bool(re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line))
        is_table = stripped.startswith("|")
        is_quote = stripped.startswith(">")
        is_html = stripped.startswith("<")

        if is_heading:
            if bold_in_section > 1:
                yield section_line, "bold-seasoning", f"{bold_in_section} bold terms in one section. At most one, and only if load-bearing."
            bold_in_section = 0
            section_line = i
            heading_text = stripped.lstrip("#").strip()
            if "—" in heading_text or " - " in heading_text or re.search(r":\s+\S+(?:\s+\S+){5,}$", heading_text):
                yield i, "heading-gloss", "Heading carries a gloss. Use a bare heading and put the explanation in the body."
            if word_count(heading_text) > 12:
                yield i, "heading-long", "Heading over 12 words. Read it cold. Does it parse alone?"
            prev_heading = heading_text
            prev_prose = False
            continue

        if is_table:
            cells = [c for c in stripped.strip("|").split("|")]
            if re.match(r"^\|?\s*:?-{3,}", stripped):
                if len(cells) > 4:
                    yield i, "table-wide", f"{len(cells)} columns. Four maximum."
            else:
                for c in cells:
                    c = c.strip()
                    if c and re.search(r"[.!?]\s+[A-Z]", c):
                        yield i, "table-sentence", "A cell holds more than one sentence. Cells are fragments."
                        break
                    if "<br" in c:
                        yield i, "table-break", "Line break inside a cell. One fact per cell."
                        break
            prev_prose = False
            continue

        if is_html or is_quote:
            prev_prose = False
            continue

        # Prose or list item from here on.
        text = re.sub(r"`[^`]*`", " ", stripped)
        text = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", text)
        text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)

        if prev_heading is not None and not is_list:
            first = " ".join(text.lower().split()[:4])
            if first and first in prev_heading.lower() and word_count(prev_heading) >= 3:
                yield i, "heading-restated", "First line repeats the heading. Say it once."
        prev_heading = None

        if prev_prose and not is_list:
            yield i, "hard-wrap", "Paragraph is hard-wrapped. One paragraph is one line."
        prev_prose = not is_list

        if "—" in text or "–" in text:
            yield i, "em-dash", "Em-dash aside. Use a full stop and two sentences."
        if ";" in text:
            yield i, "semicolon", "Semicolon. Use a full stop."
        if re.search(r"\band/or\b", text, re.I):
            yield i, "and-or", "'and/or'. Write 'and' or 'or'."
        elif re.search(r"\b\w+/\w+\b", text) and not re.search(r"https?://|\w+/\w+/\w+|\.\w+/|/\w+\.\w+|\w+/\*", text):
            yield i, "slash", "Slash as a conjunction. Write 'and' or 'or'."
        if text.count(":") > 1:
            yield i, "colon-stack", "More than one colon in a line. One colon, only for a list or quote."
        if re.match(r"^\s*\(.*\)\s*$", text) is None and re.search(r"\([^)]{40,}\)", text):
            yield i, "parenthetical", "Long parenthetical. It is an em-dash aside with different punctuation. Use a full stop."
        for sym, word in SYMBOLS.items():
            if sym in text:
                yield i, "symbol", f"'{sym}' in prose. Write '{word}'."
        if re.search(r"\bnot (?:a|an)\b.*\bbut (?:a|an)\b", text, re.I) or re.search(r"\bnot (?:just|only)\b.*\bbut\b", text, re.I):
            yield i, "not-x-but-y", "'Not X but Y' construction. State Y."

        bold_in_section += len(re.findall(r"\*\*[^*]+\*\*", stripped))
        if re.search(r"^\s*(?:[-*+]\s+)?\*\*[^*]+\*\*\s*$", stripped):
            yield i, "bold-heading", "Bold line used as a heading. Use a real heading or plain text."

        for ph in find_phrases(text, FILLER):
            yield i, "filler", f"'{ph}'. Delete it. If the meaning survives, it was wrong."
        for ph in find_phrases(text, MARKETING):
            yield i, "marketing", f"'{ph}'. Delete it or replace it with a fact."
        for ph in find_phrases(text, PREFRAME):
            yield i, "pre-frame", f"'{ph}'. Delete the whole phrase."
        for ph in find_phrases(text, PRAISE):
            yield i, "praise-opener", f"'{ph}'. Answer instead."
        for ph in find_phrases(text, list(LONG_WORDS)):
            yield i, "long-word", f"'{ph}'. Write '{LONG_WORDS[ph]}'."
        for ph in find_phrases(text, list(PHRASAL)):
            yield i, "phrasal-verb", f"'{ph}'. Write '{PHRASAL[ph]}'."
        for m2 in NOMINAL.finditer(text):
            yield i, "nominalization", f"'{m2.group(0)}'. Use the verb."
        for m2 in PASSIVE.finditer(text):
            yield i, "passive", f"'{m2.group(0)}'. Put the actor first."
        if re.search(r"\b\w+,\s+\w+,\s+and\s+\w+\b", text) and word_count(text) < 30:
            yield i, "rule-of-three", "Three-item cadence. Say the one thing that is load-bearing."

        for s in split_sentences(text):
            n = word_count(s)
            if n > SENTENCE_MAX:
                yield i, "long-sentence", f"{n} words. Cap is {SENTENCE_MAX}. Split it."
            if s.count(",") > COMMA_MAX:
                yield i, "comma-stack", f"{s.count(',')} commas in one sentence. It is probably two sentences."

    if bold_in_section > 1:
        yield section_line, "bold-seasoning", f"{bold_in_section} bold terms in one section. At most one, and only if load-bearing."


def lint_text(text):
    return [{"line": ln, "rule": rule, "standard_rule": STANDARD_RULE[rule], "detail": f"Rule {STANDARD_RULE[rule]}. {detail}"}
            for ln, rule, detail in lint_lines(text.splitlines(True))]


def main(argv):
    as_json = "--json" in argv
    files = [a for a in argv if not a.startswith("--")]
    results = {}
    if not files:
        results["<stdin>"] = lint_text(sys.stdin.read())
    for f in files:
        with open(f, encoding="utf-8") as fh:
            results[f] = lint_text(fh.read())
    if as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
    for f, findings in results.items():
        if not findings:
            print(f"{f}: clean")
            continue
        for x in findings:
            print(f"{f}:{x['line']}: {x['rule']}: {x['detail']}")
        counts = {}
        for x in findings:
            counts[x["rule"]] = counts.get(x["rule"], 0) + 1
        summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
        noun = "finding" if len(findings) == 1 else "findings"
        print(f"{f}: {len(findings)} {noun} ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
