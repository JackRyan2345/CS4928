#!/usr/bin/env python3
"""Audit check: effect of commits after the 1 Sep 2024 cut-off on the RQ1 counts.

The fitnesse and connectbot M2 runs were mined up to Dec 2024 instead of the
frozen 1 Sep 2024 cut-off. This script counts how many of those post-cut-off
commits are in the RefactoringMiner JSON and how many refactoring instances
they add, using the same rules as rq1_analysis.py (left-side path contains
"test" -> Test, otherwise Prod; duplicate refactorings in a commit counted once).

The commit lists (*_post_cutoff_commits.out) are every commit reachable from
the run's end SHA with a commit date on or after 2024-09-01, taken from the
GitHub API (/repos/{owner}/{repo}/commits?sha=END&since=2024-09-01T00:00:00Z).

Usage: python3 verification/late_effect.py RM_JSON COMMIT_LIST
Standard library only.
"""
import json
import sys


def main():
    json_path, list_path = sys.argv[1], sys.argv[2]
    late = set(open(list_path).read().split())
    commits = json.load(open(json_path))["commits"]
    in_json = with_refs = prod = test = 0
    for c in commits:
        if c["sha1"] not in late:
            continue
        in_json += 1
        seen = set()
        for r in c["refactorings"]:
            key = json.dumps(r, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            left = [loc["filePath"] for loc in r.get("leftSideLocations", [])] or [None]
            types = {"Test" if p and "test" in p.lower() else "Prod" for p in left}
            prod += "Prod" in types
            test += "Test" in types
        with_refs += bool(seen)
    print(f"{json_path}")
    print(f"  post-cut-off commits listed: {len(late)}")
    print(f"  of those in the JSON:        {in_json}")
    print(f"  with refactorings:           {with_refs}")
    print(f"  prod instances added:        {prod}")
    print(f"  test instances added:        {test}")


if __name__ == "__main__":
    main()
