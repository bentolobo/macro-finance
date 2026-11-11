"""v8 -> v9 transform for Chapter 1.

Moves (nothing is deleted outright):
  * "About this edition" version history         -> Instructor Guide
  * How to Use This Book (+ Ex 1.1)              -> Preface (index.qmd), as Exhibit P.1
  * The Top Ten (+ Ex 1.18, 1.19)                -> front/top-ten.qmd, as Exhibits P.2, P.3
  * The Twenty Questions (+ Ex 1.17)             -> Instructor Guide (optional course map)
  * Problem 1.16 (sealed Twenty-Questions essay) -> Instructor Guide; 1.17-1.19 renumbered
  * Appendix 1A Author Notes                     -> Instructor Guide
Presentation: section ids + @sec cross-refs, exhibits renumbered 1.1-1.18,
boxed features converted to styled callouts.
"""
import re, sys
from pathlib import Path

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
s = SRC.read_text()
moved = {}

def cut(start_pat, end_pat, key, include_end=False):
    """Remove text from start_pat up to (not incl.) end_pat; stash under key."""
    global s
    i = s.index(start_pat)
    j = s.index(end_pat, i + len(start_pat)) if end_pat else len(s)
    if include_end:
        j += len(end_pat)
    moved[key] = s[i:j]
    s = s[:i] + s[j:]

# ---------------------------------------------------------------- 1. moves
cut("> **About this edition.**", "```{python}\n#| label: glance", "edition")
cut("## How to Use This Book · The Learning System", "## What Makes International Finance Different", "howto")
cut("## The Twenty Questions: What Each Chapter Asks", "## The Top Ten Things to Know", "twenty")
cut("## The Top Ten Things to Know in International Finance", "## How This Book Handles Data", "topten")
cut("## Appendix 1A · Author Notes", None, "authornotes")
cut("**1.16** Choose any one of the twenty chapter questions", "### D · AI in International Finance", "p116")

# vintage line where the edition box was
s = s.replace("```{python}\n#| label: glance",
              "::: {.vintage}\nData in this chapter were last refreshed on **`{python} refresh_date()`**. "
              "Every chart names its source and retrieval date beneath it.\n:::\n\n```{python}\n#| label: glance", 1)

# problems renumber 1.17-1.19 -> 1.16-1.18
for old, new in [("1.17", "1.16"), ("1.18", "1.17"), ("1.19", "1.18")]:
    s = s.replace(f"**{old}**", f"**{new}**")

# ------------------------------------------------------- 2. section ids/refs
SEC = {"What Makes International Finance Different": "sec-frictions",
       "How Big Is Global Finance?": "sec-scale",
       "Who Is in This Market?": "sec-participants",
       "Three Kinds of Currency Exposure": "sec-exposure",
       "Has Globalization Stalled?": "sec-globalization",
       "How This Book Handles Data": "sec-data",
       "AI in International Finance": "sec-ai",
       "Live Data Lab · Taking the temperature of the global economy": "sec-lab"}
for h, sid in SEC.items():
    assert f"\n## {h}\n" in s, h
    s = s.replace(f"\n## {h}\n", f"\n## {h} {{#{sid}}}\n", 1)

# specific prose that pointed at moved sections
REPL = [
 ("Section 1.6 restates the entire book as twenty questions, one per chapter, for exactly that purpose.",
  "The Top Ten at the front of the book compresses the whole field into ten propositions for exactly that purpose."),
 ("Section 1.10's Live Data Lab", "The Live Data Lab (@sec-lab)"),
 ("proposition 9 of §1.7", "proposition 9 of the Top Ten"),
 ("proposition 4 of §1.7", "proposition 4 of the Top Ten"),
 ("your mind; §1.9.5 is about", "your mind; the Trap box below is about"),
 ("proposition 10 of §1.7", "proposition 10 of the Top Ten"),
 ("Of the Top Ten propositions in §1.7,", "Of the Top Ten propositions at the front of the book,"),
 ("**1.15** Section 1.7 states that two of the Top Ten propositions",
  "**1.15** The Top Ten, at the front of the book, states that two of its propositions"),
]
for a, b in REPL:
    assert a in s, a
    s = s.replace(a, b)
s = s.replace("of the Top Ten", "of the [Top Ten](../front/top-ten.qmd)")
OLD2SEC = {"1": "sec-frictions", "2": "sec-scale", "3": "sec-participants", "4": "sec-exposure",
           "5": "sec-globalization", "8": "sec-data", "9": "sec-ai", "10": "sec-lab"}
def secref(m):
    n = m.group(1)
    if n not in OLD2SEC:
        raise ValueError(f"stale §1.{n}")
    return "@" + OLD2SEC[n]
s = re.sub(r"§1\.(\d+)\b", secref, s)

# --------------------------------------------------------- 3. exhibit numbers
CH_MAP = {**{n: n - 1 for n in range(2, 17)}, 20: 16, 21: 17, 22: 18}
GUIDE_MAP = {1: "P.1", 17: "G.1", 18: "P.2", 19: "P.3"}
def renum_factory(chapter):
    def one(n):
        n = int(n)
        if n in CH_MAP:
            return f"1.{CH_MAP[n]}"
        if chapter:
            raise ValueError(f"chapter still references moved Exhibit 1.{n}")
        return GUIDE_MAP[n]
    def renum(m):
        return re.sub(r"1\.(\d+)", lambda k: one(k.group(1)), m.group(0))
    return renum
EXPAT = r"(?:Exhibits?|Exs?\.?)\s+1\.\d+(?:\s*(?:–|-|,|and|&|or)\s*1\.\d+)*"
s = re.sub(EXPAT, renum_factory(True), s)

# ---------------------------------------------------------- 4. callout boxes
converted = []
# Before You Read: whole block up to Market Moment
i = s.index("### Before You Read {.unnumbered}"); j = s.index("## Market Moment")
blk = s[i:j].replace("### Before You Read {.unnumbered}\n", "")
blk = re.sub(r"(?m)^> ?", "", blk).strip()
s = s[:i] + "::: {.callout-note .mf-box .mf-activity icon=false}\n## Before You Read\n\n" + blk + "\n:::\n\n" + s[j:]
converted.append(("activity", "Before You Read"))

KIND = [("Trap", "trap"), ("single most expensive error", "trap"), ("Gross versus net", "trap"),
        ("Ethics in Practice", "ethics"), ("Policy Debate", "debate"),
        ("Explain It", "activity"), ("Revisit", "activity"), ("Interactive practice", "activity"),
        ("central asymmetry", "keyidea"), ("Reading a data vintage", "keyidea"),
        ("Why this section exists", "note"), ("A note on these sources", "note")]
def kind_of(title):
    for k, v in KIND:
        if k in title:
            return v
    return "note"

lines = s.split("\n"); out = []; i = 0
while i < len(lines):
    L = lines[i]
    if L.startswith("### ") and i + 2 < len(lines) and lines[i+1] == "" and lines[i+2].startswith(">"):
        title = L[4:].strip(); j = i + 2; body = []
        while j < len(lines) and lines[j].startswith(">"):
            body.append(re.sub(r"^> ?", "", lines[j])); j += 1
        k = kind_of(title); converted.append((k, title))
        out += [f"::: {{.callout-note .mf-box .mf-{k} icon=false}}", f"## {title}", ""] + body + [":::"]
        i = j; continue
    out.append(L); i += 1
s = "\n".join(out)

# Worked Application: heading through to next heading
def wrap_section(head_prefix, cls):
    global s
    i = s.index(head_prefix)
    j = min(x for x in (s.find("\n## ", i + 5), s.find("\n### ", i + 5)) if x > 0)
    block = s[i:j].rstrip("\n")
    title, body = block.split("\n", 1)
    s = s[:i] + f"::: {{.callout-note .mf-box .mf-{cls} icon=false}}\n## {title[4:]}\n{body}\n:::\n" + s[j:]
    converted.append((cls, title[4:]))
wrap_section("### Worked Application 1.1", "application")

# Learning objectives as a card
i = s.index("## Learning Objectives {.unnumbered}"); j = s.index("\n## ", i + 5)
head, body = s[i:j].split("\n", 1)
s = s[:i] + head + "\n\n::: {.objectives}\n" + body.strip() + "\n:::\n" + s[j:]

# ------------------------------------------------------------------ 5. check
for bad in ["Twenty Questions", "Appendix 1A", "§1."]:
    if bad in s:
        print("WARN still contains:", bad)
OUT.write_text(s)
Path(sys.argv[3]).mkdir(parents=True, exist_ok=True)
for k, v in moved.items():
    if k in ("authornotes", "edition", "twenty", "p116"):
        v = re.sub(EXPAT, renum_factory(False), v)
        v = re.sub(r"§1\.(\d+)\b", lambda m: {"6": "the Twenty Questions (this guide)",
                                               "7": "the Top Ten (front matter)",
                                               "8": "§1.6", "9": "§1.7", "10": "§1.8"}.get(m.group(1), m.group(0)), v)
    else:  # front matter: exhibits P.x
        v = re.sub(EXPAT, renum_factory(False), v)
    (Path(sys.argv[3]) / f"{k}.md").write_text(v)
print("converted boxes:"); [print("  ", k, "|", t[:70]) for k, t in converted]
print("moved:", {k: len(v.split()) for k, v in moved.items()})
