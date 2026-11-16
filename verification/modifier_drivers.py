#!/usr/bin/env python3
"""Audit check: which projects and commits drive the test-code top types.

Our M2 test-code top 5 contains ADD_VARIABLE_MODIFIER and ADD_PARAMETER_MODIFIER,
which are not in the paper's test top 5. For each project this script counts
test-code instances of those two types (plus ADD_METHOD_ANNOTATION for
comparison) and the share that falls in the project's 3 largest commits, to
show whether the types come from steady refactoring or a few bulk commits.

Same rules as rq1_analysis.py: a refactoring is test code if any left-side
location path contains "test" (lowercased); duplicates in a commit counted once.

Usage: python3 verification/modifier_drivers.py RM_JSON [RM_JSON ...]
Standard library only.
"""
import json
import sys
from collections import Counter

TYPES = ["Add Parameter Modifier", "Add Variable Modifier", "Add Method Annotation"]


def main():
    totals = Counter()
    rows = []
    for path in sorted(sys.argv[1:]):
        commits = json.load(open(path))["commits"]
        per_type = {t: Counter() for t in TYPES}
        for c in commits:
            seen = set()
            for r in c["refactorings"]:
                key = json.dumps(r, sort_keys=True)
                if key in seen or r["type"] not in per_type:
                    continue
                seen.add(key)
                left = [loc["filePath"] for loc in r.get("leftSideLocations", [])]
                if any("test" in p.lower() for p in left):
                    per_type[r["type"]][c["sha1"][:8]] += 1
        cells = []
        for t in TYPES:
            n = sum(per_type[t].values())
            totals[t] += n
            top3 = sum(k for _, k in per_type[t].most_common(3))
            cells.append(f"{n} ({100 * top3 / n:.0f}% in top-3 commits)" if n else "0")
        rows.append((path, cells))

    print("project file | " + " | ".join(f"test {t}" for t in TYPES))
    for path, cells in rows:
        print(f"{path} | " + " | ".join(cells))
    print("TOTAL | " + " | ".join(str(totals[t]) for t in TYPES))


if __name__ == "__main__":
    main()
