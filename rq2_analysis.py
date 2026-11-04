#!/usr/bin/env python3
"""RQ2 concentration analysis (frozen M1 rule) over RefactoringMiner JSON.

Rule (M1_Freeze_Info): restrict to commits that refactor both production and
test code; link a production class to the commit's test files only when the
commit refactors exactly one production class; cross-check against Foo/FooTest
naming. Concentrated if the top 10% of production classes account for >= 50%
of linked test refactorings; otherwise diffuse.

Operationalisation (same labels as rq1_analysis.py):
  - a refactoring is Test/Prod by its left-side locations' paths ("test" substring)
  - production class = production .java file path (top-level class per file)
  - module = path prefix before "/src/" (Maven/Gradle module), "." if none

Usage: python3 rq2_analysis.py [-o OUT_DIR] JSON_OR_DIR [...]
"""
import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from rq1_analysis import code_type, load_projects


def module_of(path):
    return path.split("/src/")[0] if "/src/" in path else "."


def stem(path):
    return Path(path).stem


def naming_match(prod_path, test_path):
    """Foo -> FooTest/FooTests/FooIT/TestFoo/FooTestCase."""
    p, t = stem(prod_path), stem(test_path)
    return bool(re.fullmatch(rf"(Test)?{re.escape(p)}(Test|Tests|IT|TestCase)?", t)) and p != t


def analyze(commits):
    linked = Counter()            # prod class -> test refactorings
    naming = Counter()            # prod class -> test refactorings in name-matched test files
    stats = Counter()
    for sha, refs in commits.items():
        seen, prod_files, test_refs = set(), set(), []
        for r in refs:
            key = json.dumps(r, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            left = [l["filePath"] for l in r.get("leftSideLocations", [])] or [None]
            types = {code_type(p) for p in left}
            if "Prod" in types:
                prod_files.update(p for p in left if p and code_type(p) == "Prod" and p.endswith(".java"))
            if "Test" in types:
                test_refs.append([p for p in left if p and code_type(p) == "Test"])
        if not prod_files or not test_refs:
            continue
        stats["cooccur_commits"] += 1
        stats["cooccur_test_refactorings"] += len(test_refs)
        if len(prod_files) != 1:
            continue
        cls = next(iter(prod_files))
        stats["single_class_commits"] += 1
        linked[cls] += len(test_refs)
        naming[cls] += sum(1 for paths in test_refs if any(naming_match(cls, t) for t in paths))
    return linked, naming, stats


def concentration(counter):
    vals = sorted(counter.values(), reverse=True)
    if not vals:
        return 0, 0.0
    k = max(1, math.ceil(len(vals) * 0.10))
    return k, sum(vals[:k]) / sum(vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", default="rq2_results")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    projects = load_projects(args.inputs)
    summary, classes, modules = [], [], Counter()
    pooled = Counter()
    for name in sorted(projects):
        linked, naming, s = analyze(projects[name])
        k, share = concentration(linked)
        total = sum(linked.values())
        summary.append([name, s["cooccur_commits"], s["single_class_commits"], s["cooccur_test_refactorings"],
                        total, len(linked), k, round(share * 100, 1),
                        round(sum(naming.values()) / total * 100, 1) if total else "",
                        "concentrated" if share >= 0.5 else "diffuse"])
        for cls, n in linked.items():
            pooled[(name, cls)] = n
            modules[(name, module_of(cls))] += n
            classes.append([name, module_of(cls), cls, n, naming[cls]])

    k, share = concentration(pooled)
    with open(out / "rq2_per_project.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["project", "cooccur_commits", "single_prod_class_commits", "cooccur_test_refactorings",
                    "linked_test_refactorings", "linked_prod_classes", "top10pct_k", "top10pct_share_%",
                    "naming_match_%", "verdict"])
        w.writerows(summary)
        w.writerow(["POOLED", "", "", "", sum(pooled.values()), len(pooled), k, round(share * 100, 1), "",
                    "concentrated" if share >= 0.5 else "diffuse"])
    classes.sort(key=lambda r: -r[3])
    with open(out / "rq2_classes.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["project", "module", "prod_class_file", "linked_test_refactorings", "name_matched_test_refactorings"])
        w.writerows(classes)
    with open(out / "rq2_modules.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["project", "module", "linked_test_refactorings"])
        w.writerows([[p, m, n] for (p, m), n in modules.most_common()])

    for row in summary:
        print(row)
    print(f"POOLED: top {k}/{len(pooled)} classes = {share * 100:.1f}% of {sum(pooled.values())} linked test refactorings")


if __name__ == "__main__":
    main()
