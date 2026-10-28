#!/usr/bin/env python3
"""RQ1 tables from RefactoringMiner JSON, in the format of Horikawa et al. (ICSME 2025).

Mirrors the authors' analyze/src/rq1_freq/analysis.py and rq1_type scripts
(replication package: github.com/Mont9165/ProdTestRefactoringAndMetrics):
  - each left-side location is Test if its lowercased path contains "test",
    otherwise Prod (a refactoring with no left-side location counts as Prod)
  - a commit is Prod-only, Test-only or Co-occurring by the set of those labels
  - refactored files = unique left and right paths of the locations' refactorings
  - a refactoring counts once for each code type it touches

Usage: python3 rq1_analysis.py [-o OUT_DIR] JSON_OR_DIR [JSON_OR_DIR ...]
Standard library only. Writes CSVs, a Markdown Table I and an SVG of Fig. 2.
"""
import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

# RefactoringType display names whose enum name (used in the paper) differs
# from the upper-cased display name; taken from RefactoringMiner 3.0.0.
ENUM_NAMES = {
    "Extract Method": "EXTRACT_OPERATION",
    "Move And Rename Attribute": "MOVE_RENAME_ATTRIBUTE",
    "Inline Method": "INLINE_OPERATION",
    "Move Method": "MOVE_OPERATION",
    "Move And Rename Method": "MOVE_AND_RENAME_OPERATION",
    "Pull Up Method": "PULL_UP_OPERATION",
    "Move And Rename Class": "MOVE_RENAME_CLASS",
    "Push Down Method": "PUSH_DOWN_OPERATION",
    "Extract And Move Method": "EXTRACT_AND_MOVE_OPERATION",
    "Move And Inline Method": "MOVE_AND_INLINE_OPERATION",
    "Change Method Access Modifier": "CHANGE_OPERATION_ACCESS_MODIFIER",
    "Merge Method": "MERGE_OPERATION",
    "Split Method": "SPLIT_OPERATION",
}

TABLE1_COLUMNS = [
    ("Refactoring commits", "Prod. commits", "prod_commits"),
    ("Refactoring commits", "Test commits", "test_commits"),
    ("Refactoring commits", "Co-occur. commits", "cooccur_commits"),
    ("Refactored files", "Prod. code", "prod_files"),
    ("Refactored files", "Test code", "test_files"),
    ("Refactoring instances", "Prod. code", "prod_refactorings"),
    ("Refactoring instances", "Test code", "test_refactorings"),
]


def type_name(display_name):
    return ENUM_NAMES.get(display_name, display_name.upper().replace(" ", "_"))


def code_type(path):
    return "Test" if path and "test" in path.lower() else "Prod"


def project_name(repository_url, fallback):
    if not repository_url:
        return fallback
    parts = repository_url.rstrip("/").removesuffix(".git").split("/")
    return "_".join(parts[-2:]) if len(parts) >= 2 else fallback


def load_projects(paths):
    """Return {project: {sha1: [refactoring, ...]}}, merging files of the same project."""
    files = []
    for p in map(Path, paths):
        files.extend(sorted(p.glob("*.json")) if p.is_dir() else [p])
    projects = defaultdict(dict)
    for f in files:
        with open(f) as fh:
            commits = json.load(fh)["commits"]
        for c in commits:
            name = project_name(c.get("repository"), f.stem)
            projects[name][c["sha1"]] = c["refactorings"]
    return projects


def analyze_project(commits):
    stats = Counter()
    files = {"Prod": set(), "Test": set()}
    type_counts = {"Prod": Counter(), "Test": Counter()}
    for sha1, refactorings in commits.items():
        commit_types = set()
        seen = set()
        for r in refactorings:
            # stands in for the authors' hash of commit + type + refactoring contents;
            # same-description entries with different locations are distinct refactorings
            key = json.dumps(r, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            left = [loc["filePath"] for loc in r.get("leftSideLocations", [])] or [None]
            right = [loc["filePath"] for loc in r.get("rightSideLocations", [])]
            r_types = set()
            for path in left:
                t = code_type(path)
                r_types.add(t)
                files[t].update(p for p in [path, *right] if p)
            for t in r_types:
                stats[f"{t.lower()}_refactorings"] += 1
                type_counts[t][type_name(r["type"])] += 1
            commit_types |= r_types
        if not seen:
            continue
        stats["refactoring_commits"] += 1
        stats["total_refactorings"] += len(seen)
        if commit_types == {"Prod", "Test"}:
            stats["cooccur_commits"] += 1
        elif commit_types == {"Prod"}:
            stats["prod_commits"] += 1
        else:
            stats["test_commits"] += 1
    stats["analyzed_commits"] = len(commits)
    stats["prod_files"] = len(files["Prod"])
    stats["test_files"] = len(files["Test"])
    return stats, type_counts


def describe(values):
    """Total, Mean, Median, Variance, Standard Deviation, Min, Max (sample variance, as in the paper's CSVs)."""
    if not values:
        return ["", "", "", "", "", "", ""]
    var = statistics.variance(values) if len(values) > 1 else ""
    sd = statistics.stdev(values) if len(values) > 1 else ""
    return [sum(values), statistics.mean(values), statistics.median(values), var, sd, min(values), max(values)]


def write_csv(path, header, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def write_table1(out, per_project):
    """Table I: Mean / Median / Sum across projects, truncated to int, Sum with group percentages."""
    keys = [k for _, _, k in TABLE1_COLUMNS]
    columns = {k: [s[k] for s in per_project.values()] for k in keys}
    sums = {k: sum(v) for k, v in columns.items()}
    groups = defaultdict(list)
    for group, _, k in TABLE1_COLUMNS:
        groups[group].append(k)
    sum_row = []
    for group, _, k in TABLE1_COLUMNS:
        group_total = sum(sums[g] for g in groups[group])
        pct = f" ({sums[k] / group_total * 100:.1f}%)" if group_total else ""
        sum_row.append(f"{sums[k]:,}{pct}")
    rows = [
        ["Mean"] + [f"{int(statistics.mean(columns[k])):,}" for k in keys],
        ["Median"] + [f"{int(statistics.median(columns[k])):,}" for k in keys],
        ["Sum"] + sum_row,
    ]
    write_csv(out / "table1.csv", ["Type"] + [f"{g} - {c}" for g, c, _ in TABLE1_COLUMNS], rows)

    md = ["| Type | " + " | ".join(f"{g}<br>{c}" for g, c, _ in TABLE1_COLUMNS) + " |",
          "|---|" + "---:|" * len(TABLE1_COLUMNS)]
    md += ["| " + " | ".join(row) + " |" for row in rows]
    (out / "table1.md").write_text("\n".join(md) + "\n")
    return rows


def write_summary_freq(out, per_project):
    metrics = [
        ("Refactoring Commits", "refactoring_commits"),
        ("Total Refactorings", "total_refactorings"),
        ("Test Refactorings", "test_refactorings"),
        ("Production Refactorings", "prod_refactorings"),
        ("Avg Refactorings per Commit (Total)", None),
        ("Unique Test Files Changed", "test_files"),
        ("Unique Production Files Changed", "prod_files"),
        ("Test-Only Commits", "test_commits"),
        ("Production-Only Commits", "prod_commits"),
        ("Mixed Commits", "cooccur_commits"),
    ]
    rows = []
    for label, key in metrics:
        if key:
            values = [s[key] for s in per_project.values()]
        else:
            values = [s["total_refactorings"] / s["refactoring_commits"]
                      for s in per_project.values() if s["refactoring_commits"]]
        rows.append([label] + describe(values))
    write_csv(out / "RQ1_summary_freq.csv",
              ["Metric", "Total", "Mean", "Median", "Variance", "Standard Deviation", "Min", "Max"], rows)


def write_types(out, type_counts_by_project):
    """Per-type stats over the projects where the type occurs, plus share of all refactorings of that code type."""
    totals, pct = {}, {}
    for t, label in [("Prod", "prod"), ("Test", "test")]:
        per_type = defaultdict(list)
        for counts in type_counts_by_project.values():
            for name, n in counts[t].items():
                per_type[name].append(n)
        grand = sum(sum(v) for v in per_type.values())
        totals[t] = {name: sum(v) for name, v in per_type.items()}
        pct[t] = {name: n / grand * 100 for name, n in totals[t].items()} if grand else {}
        rows = [[name] + describe(v) + [pct[t][name]]
                for name, v in sorted(per_type.items(), key=lambda kv: -sum(kv[1]))]
        rows.append(["Total", grand, "", "", "", "", "", "", 100 if grand else ""])
        write_csv(out / f"RQ1_{label}_types.csv",
                  ["Refactoring Type", "Total", "Mean", "Median", "Variance", "Standard Deviation",
                   "Min", "Max", "Percentage"], rows)

    names = set(totals["Prod"]) | set(totals["Test"])
    rows = []
    for name in names:
        p, t = pct["Prod"].get(name, 0), pct["Test"].get(name, 0)
        rows.append([name, totals["Prod"].get(name, 0), p, totals["Test"].get(name, 0), t,
                     p / t if t else "", t / p if p else "", (p + t) / 2])
    rows.sort(key=lambda r: (r[5] == "", -(r[5] or 0), -r[7]))
    write_csv(out / "RQ1_type_comparison.csv",
              ["Refactoring Type", "Production Total", "Production Percentage", "Test Total",
               "Test Percentage", "Production[%] / Test[%]", "Test[%] / Production[%]",
               "(Production[%] + Test[%])/2"], rows)
    return rows


def write_fig2(out, comparison_rows, top_n=40):
    """Fig. 2: top-N types by Prod% + Test%, as in the authors' rq1_type/graph.py."""
    top = sorted(comparison_rows, key=lambda r: -(r[2] + r[4]))[:top_n]
    write_csv(out / "fig2_data.csv", ["Refactoring Type", "Production Percentage", "Test Percentage"],
              [[r[0], r[2], r[4]] for r in top])

    label_w, plot_w, row_h, bar_h, top_pad = 300, 420, 22, 8, 40
    max_pct = max([max(r[2], r[4]) for r in top] + [1])
    step = 2 if max_pct <= 14 else 5
    x_max = (int(max_pct / step) + 1) * step
    height = top_pad + row_h * len(top) + 50
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{label_w + plot_w + 30}" height="{height}" '
           'font-family="sans-serif" font-size="11">',
           '<rect width="100%" height="100%" fill="white"/>']
    for tick in range(0, x_max + 1, step):
        x = label_w + tick / x_max * plot_w
        svg.append(f'<line x1="{x:.1f}" y1="{top_pad - 5}" x2="{x:.1f}" y2="{top_pad + row_h * len(top)}" '
                   'stroke="#ddd" stroke-dasharray="3,3"/>')
        svg.append(f'<text x="{x:.1f}" y="{top_pad + row_h * len(top) + 15}" text-anchor="middle">{tick}</text>')
    for i, (name, p, t) in enumerate((r[0], r[2], r[4]) for r in top):
        y = top_pad + i * row_h
        svg.append(f'<text x="{label_w - 6}" y="{y + row_h / 2 + 4}" text-anchor="end">{name}</text>')
        svg.append(f'<rect x="{label_w}" y="{y + 3}" width="{p / x_max * plot_w:.1f}" height="{bar_h}" fill="#e8696b"/>')
        svg.append(f'<rect x="{label_w}" y="{y + 3 + bar_h}" width="{t / x_max * plot_w:.1f}" height="{bar_h}" fill="#7aaee0"/>')
    svg.append(f'<text x="{label_w + plot_w / 2}" y="{height - 12}" text-anchor="middle">Percentage [%]</text>')
    lx = label_w + plot_w - 130
    svg.append(f'<rect x="{lx}" y="10" width="12" height="10" fill="#e8696b"/>'
               f'<text x="{lx + 17}" y="19">Production Code</text>')
    svg.append(f'<rect x="{lx}" y="24" width="12" height="10" fill="#7aaee0"/>'
               f'<text x="{lx + 17}" y="33">Test Code</text>')
    svg.append("</svg>")
    (out / "fig2.svg").write_text("\n".join(svg) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="RefactoringMiner JSON files, or directories of them")
    ap.add_argument("-o", "--out", default="rq1_results", help="output directory (default: rq1_results)")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    projects = load_projects(args.inputs)

    per_project, type_counts = {}, {}
    for name in sorted(projects):
        per_project[name], type_counts[name] = analyze_project(projects[name])

    keys = ["analyzed_commits", "refactoring_commits", "total_refactorings"] + [k for _, _, k in TABLE1_COLUMNS]
    write_csv(out / "per_project.csv", ["project"] + keys,
              [[name] + [s[k] for k in keys] for name, s in per_project.items()])
    table1 = write_table1(out, per_project)
    write_summary_freq(out, per_project)
    comparison = write_types(out, type_counts)
    write_fig2(out, comparison)

    print(f"{len(per_project)} projects: {', '.join(per_project)}")
    print((out / "table1.md").read_text())
    print("Top 5 types (Prod / Test %):")
    top = sorted(comparison, key=lambda r: -(r[2] + r[4]))[:5]
    for r in top:
        print(f"  {r[0]:<35} {r[2]:5.1f}  {r[4]:5.1f}")
    print(f"Wrote results to {out}/")


if __name__ == "__main__":
    main()