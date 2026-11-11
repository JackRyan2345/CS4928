#!/usr/bin/env python3
"""M4 evidence: annotation and test-framework-annotation refactorings in test code.

Regenerates the figures behind the M4 design problem from the committed
RefactoringMiner JSON, using the same rules as rq1_analysis.py:
  - a refactoring is test code if any left-side location path contains "test"
  - duplicate refactorings within a commit are counted once
  - an "annotation refactoring" is any type whose name contains "Annotation"
  - the annotation name is the first @Name in the refactoring description
  - a "framework annotation" is one of the JUnit annotations in FRAMEWORK

Optional:
  --clones DIR  directory holding project clones (e.g. ../../M4); adds the date
                and subject of each top commit. Clone dir = project name after
                the first "_" (jdbi_jdbi -> jdbi).
  --scan DIR    count JUnit 4 and JUnit 5 test files in a checkout.

Usage:
  python3 m4_annotation_analysis.py [-o OUT] [--clones DIR] [--scan DIR ...]
Standard library only. Defaults read */m2_reproduction_results and */event_a_results.
"""
import argparse
import csv
import glob
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from rq1_analysis import code_type, load_projects

FRAMEWORK = {
    "Test", "Before", "After", "BeforeClass", "AfterClass", "BeforeEach", "AfterEach",
    "BeforeAll", "AfterAll", "Rule", "ClassRule", "RunWith", "ExtendWith",
    "RegisterExtension", "Ignore", "Disabled", "Category", "Tag", "FixMethodOrder",
    "TestMethodOrder", "ParameterizedTest", "Parameters", "Parameter", "DisplayName",
    "Nested", "Timeout", "TempDir", "ValueSource", "MethodSource", "CsvSource",
}
SAMPLES = {"M2": "*/m2_reproduction_results", "Event_A": "*/event_a_results"}
TOP_N = 5
JUNIT4_IMPORT = re.compile(r"import org\.junit\.(Test|Before|After|Rule|Ignore|runner)")
JUNIT5_IMPORT = re.compile(r"import org\.junit\.jupiter")


def annotation_name(description):
    m = re.search(r"@([A-Za-z.]+)", description)
    return m.group(1).split(".")[-1] if m else ""


def test_refactorings(commits):
    """Yield (sha, refactoring) for each unique refactoring that touches test code."""
    for sha, refs in commits.items():
        seen = set()
        for r in refs:
            key = json.dumps(r, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            if any(code_type(l["filePath"]) == "Test" for l in r.get("leftSideLocations", [])):
                yield sha, r


def commit_info(clones, project, sha):
    if not clones:
        return "", ""
    repo = Path(clones) / project.split("_", 1)[-1]
    if not (repo / ".git").exists():
        return "", ""
    out = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%ad%x09%s", "--date=short", sha],
                         capture_output=True, text=True).stdout.strip()
    return tuple(out.split("\t", 1)) if "\t" in out else ("", "")


def write_csv(path, header, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default="m4_annotation_results")
    ap.add_argument("--clones", help="directory of project clones, for commit dates/subjects")
    ap.add_argument("--scan", nargs="*", default=[], help="checkouts to count JUnit 4/5 test files in")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    share_rows, name_rows, project_rows, commit_rows = [], [], [], []
    for sample, pattern in SAMPLES.items():
        projects = load_projects(sorted(glob.glob(pattern)))
        tests = ann = fw = 0
        names = Counter()
        for project in sorted(projects):
            p_tests, p_fw = 0, 0
            fw_by_commit = Counter()
            for sha, r in test_refactorings(projects[project]):
                p_tests += 1
                if "Annotation" not in r["type"]:
                    continue
                ann += 1
                name = annotation_name(r["description"])
                names[name or "(none)"] += 1
                if name in FRAMEWORK:
                    p_fw += 1
                    fw_by_commit[sha] += 1
            tests += p_tests
            fw += p_fw
            top = fw_by_commit.most_common(TOP_N)
            top_share = sum(n for _, n in top) / p_fw * 100 if p_fw else 0
            project_rows.append([sample, project, p_tests, p_fw, round(p_fw / p_tests * 100, 1) if p_tests else 0,
                                 len(fw_by_commit), round(top_share, 1)])
            for sha, n in top:
                date, subject = commit_info(args.clones, project, sha)
                commit_rows.append([sample, project, sha, n, round(n / p_fw * 100, 1), date, subject])
        share_rows.append([sample, tests, ann, round(ann / tests * 100, 1), fw,
                           round(fw / tests * 100, 1), round(fw / ann * 100, 1)])
        name_rows += [[sample, n, c, n in FRAMEWORK] for n, c in names.most_common()]

    write_csv(out / "annotation_share.csv",
              ["sample", "test_refactorings", "annotation_refactorings", "annotation_%_of_test",
               "framework_annotation_refactorings", "framework_%_of_test", "framework_%_of_annotation"], share_rows)
    write_csv(out / "annotation_names.csv", ["sample", "annotation", "test_refactorings", "is_framework"], name_rows)
    write_csv(out / "framework_by_project.csv",
              ["sample", "project", "test_refactorings", "framework_annotation_refactorings", "framework_%_of_test",
               "commits_with_framework_annotation_refactorings", f"top{TOP_N}_commits_%"], project_rows)
    write_csv(out / "framework_top_commits.csv",
              ["sample", "project", "sha", "framework_annotation_refactorings", "%_of_project", "date", "subject"],
              commit_rows)

    if args.scan:
        rows = []
        for d in args.scan:
            j4 = j5 = 0
            for f in Path(d).rglob("*.java"):
                text = f.read_text(errors="ignore")
                j4 += bool(JUNIT4_IMPORT.search(text))
                j5 += bool(JUNIT5_IMPORT.search(text))
            head = subprocess.run(["git", "-C", d, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
            rows.append([Path(d).name, head, j4, j5])
        write_csv(out / "junit_files.csv", ["checkout", "head", "junit4_files", "junit5_files"], rows)

    for r in share_rows:
        print(f"{r[0]}: {r[2]}/{r[1]} test refactorings are annotation changes ({r[3]}%); "
              f"framework annotations {r[4]} ({r[5]}% of test, {r[6]}% of annotation)")
    print(f"Wrote results to {out}/")


if __name__ == "__main__":
    main()
