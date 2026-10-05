"""Map RAADS quiz answers to signets.

Score vector -> normalized distance from the max corner -> equal-frequency bins.
Xaddy is reserved for the exact max vector and Inntinnsic for the exact min vector;
the other signets split the rest.
"""
import csv
import itertools
import math
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
DIMS = ["SR", "SM", "CI", "L"]
MAX_SIGNET = "Xaddy"
MIN_SIGNET = "Inntinnsic"


def load_items():
    items = []
    for line in (HERE / "raads.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\d+\..*\[(.*)\]\s*$", line)
        if not m:
            continue
        effects = {}
        for part in m.group(1).split(","):
            part = part.strip()
            if part and part != "nothing":
                value, dim = part.split()
                effects[dim] = int(value)
        items.append(effects)
    return items


def load_signets():
    with open(HERE / "signets.csv", newline="", encoding="utf-8-sig") as f:
        names = [row["Signet"] for row in csv.DictReader(f)]
    return [n for n in names if n not in (MAX_SIGNET, MIN_SIGNET)]


ITEMS = load_items()
SIGNETS = load_signets()
N_BINS = len(SIGNETS)  # signets sharing the middle; the two extremes are reserved

# Score range per dimension: false adds nothing, so min is the sum of negatives, max the sum of positives.
LO = {d: sum(min(0, i.get(d, 0)) for i in ITEMS) for d in DIMS}
HI = {d: sum(max(0, i.get(d, 0)) for i in ITEMS) for d in DIMS}


def score(answers):
    """answers: iterable of 14 booleans -> tuple of dimension scores in DIMS order."""
    totals = dict.fromkeys(DIMS, 0)
    for true, effects in zip(answers, ITEMS):
        if true:
            for d, v in effects.items():
                totals[d] += v
    return tuple(totals[d] for d in DIMS)


def distance(vec):
    """Euclidean distance from the max corner in normalized (0-1) space."""
    return math.sqrt(sum(
        (1 - (v - LO[d]) / (HI[d] - LO[d])) ** 2 for v, d in zip(vec, DIMS)
    ))


MAX_VEC = tuple(HI[d] for d in DIMS)
MIN_VEC = tuple(LO[d] for d in DIMS)


def build_table():
    counts = Counter(score(a) for a in itertools.product([False, True], repeat=len(ITEMS)))
    rest = {v: c for v, c in counts.items() if v not in (MAX_VEC, MIN_VEC)}
    total = sum(rest.values())
    # Tie-break on raw sum, then SR, so the order is deterministic.
    ordered = sorted(rest, key=lambda v: (distance(v), -sum(v), -v[0], v))
    table = {MAX_VEC: MAX_SIGNET, MIN_VEC: MIN_SIGNET}
    seen = 0
    for v in ordered:
        mid = seen + rest[v] / 2  # a vector straddling a cutoff goes where its midpoint falls
        table[v] = SIGNETS[min(N_BINS - 1, int(mid / total * N_BINS))]
        seen += rest[v]
    return table, counts


TABLE, COUNTS = build_table()


def signet_for(answers):
    return TABLE[score(answers)]


if __name__ == "__main__":
    print("Ranges:", {d: (LO[d], HI[d]) for d in DIMS})
    print("Max vector:", dict(zip(DIMS, MAX_VEC)), "patterns:", COUNTS[MAX_VEC])
    print("Min vector:", dict(zip(DIMS, MIN_VEC)), "patterns:", COUNTS[MIN_VEC])
    print("Distinct score vectors:", len(COUNTS), "of", sum(COUNTS.values()), "patterns\n")
    per_signet = Counter()
    for v, s in TABLE.items():
        per_signet[s] += COUNTS[v]
    for s in [MAX_SIGNET, MIN_SIGNET] + SIGNETS:
        print(f"{per_signet[s]:6d}  {s}")
    with open(HERE / "signet_table.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(DIMS + ["distance", "patterns", "signet"])
        for v in sorted(TABLE, key=lambda v: (distance(v), -sum(v), -v[0], v)):
            w.writerow(list(v) + [f"{distance(v):.4f}", COUNTS[v], TABLE[v]])
