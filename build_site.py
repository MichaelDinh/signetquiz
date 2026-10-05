"""Generate docs/data.js (questions, scoring, score->signet table, signet info) for the quiz page."""
import csv
import json
import re

import bin_signets as b

questions = []
for line in (b.HERE / "raads.txt").read_text(encoding="utf-8").splitlines():
    m = re.match(r"^\d+\.\s*(.*?)\s*\[.*\]\s*$", line)
    if m:
        questions.append(m.group(1))
assert len(questions) == len(b.ITEMS)

with open(b.HERE / "signets.csv", newline="", encoding="utf-8-sig") as f:
    signets = {r["Signet"]: {"type": r["Type"], "description": r["Description"]} for r in csv.DictReader(f)}

data = {
    "dims": b.DIMS,
    "questions": questions,
    "effects": b.ITEMS,
    "table": {",".join(map(str, v)): s for v, s in b.TABLE.items()},
    "signets": signets,
}

out = b.HERE / "docs"
out.mkdir(exist_ok=True)
(out / "data.js").write_text(
    "const QUIZ_DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8"
)
print(f"Wrote {out / 'data.js'}: {len(questions)} questions, {len(data['table'])} score vectors, {len(signets)} signets")
