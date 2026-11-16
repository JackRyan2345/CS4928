# CS4928 G08 / P11: Refactoring in Test vs Production Code

Bounded reproduction of Horikawa et al., *"How Does Test Code Differ From Production Code in Terms of
Refactoring? An Empirical Study"*, ICSME 2025 (DOI 10.1109/ICSME64153.2025.00079).
Authors' artefact (observed only, not modified): https://github.com/Mont9165/ProdTestRefactoringAndMetrics

**RQ1:** Does refactoring differ between production and test code in frequency and type?
**RQ2:** Do a few production classes account for most test refactoring, and should the worst-affected
module's fixtures be redesigned?

## Tags (freeze points)
| Tag | Stage |
|---|---|
| `M1_PLAN` | Week 5 preregistration |
| `M2_REPRO`, `PRE_EVENT_A` | Week 7 bounded reproduction |
| `PRE_EVENT_B` | Week 9/10 M4 design decision |
| `POST_EVENT_B` | Event B response |
| `FINAL` | Final submission |

## Evidence map (Student Tracker column → evidence)
| Tracker column | Evidence |
|---|---|
| Bounded sample / case IDs | `*/m2_reproduction_results/` (RefactoringMiner JSON + start/end SHA per project) |
| Reproduction result | `rq1_results/table1.md`, `RQ1_test_types.csv`, `RQ1_prod_types.csv`, `RQ1_type_comparison.csv`, `per_project.csv`, `fig2.svg` |
| Event A result / decision | `*/event_a_results/` (JSON + SHAs), `event_a_analysis/` |
| RQ2 result | `rq2_results/rq2_per_project.csv`, `rq2_modules.csv`, `rq2_classes.csv` |
| Concrete design problem | `m4_annotation_results/annotation_share.csv`, `framework_by_project.csv`, `junit_files.csv` |
| Alternative(s) considered | `verification/m4_alternative_trials/` (Vintage trial, JUnit 5 smoke test) |
| Verification evidence (M4) | `m4/maven_release_baseline_test-log.out` (740 tests, 0 failures, 19 skipped); JDK 17 re-run in `verification/jdk17_rerun/` |
| Event B | `event_b/EVENT_B_PREDICTION.md`, `EVENT_B_RESULTS.md`, `response_A.diff`, `response_B.diff`, `surface_A.tsv`, `surface_B.tsv`, `*.out` build logs |
| Audit checks | `verification/` (see "Evidence added at FINAL") |

## Repository layout
| Path | Contents |
|---|---|
| `ciaran_results/`, `eoins_results/`, `Jacks_Results/`, `kai_results/`, `oran_results/` | Per-member RefactoringMiner output, split into `m2_reproduction_results/` and `event_a_results/` |
| `rq1_analysis.py` → `rq1_results/` | RQ1 Table I and Figure 2 (M2) |
| `rq1_analysis.py` → `event_a_analysis/` | RQ1 on held-out projects (Event A) |
| `rq2_analysis.py` → `rq2_results/`, `event_a_analysis/rq2_event_a_results/` | RQ2 concentration analysis |
| `m4_annotation_analysis.py` → `m4_annotation_results/` | Annotation / test-framework evidence for M4 |
| `m4/` | M4 verification log, exactly as committed at `PRE_EVENT_B` |
| `event_b/` | Event B prediction, responses, diffs and build logs |
| `verification/` | Evidence added at `FINAL` (see below) |

## Environment
- JDK 17 (OpenJDK 17), Maven 3.9.16, Python 3.10+ (standard library only)
- RefactoringMiner 3.0.0 (commit `ae152e1d2897074f9aa6fb3f08e6e13ba26ca4c8`, the `3.0.0` tag)
- Cut-off: commits up to 1 Sep 2024 (end SHA per project in each `*_sha` / `*SHA` file)

## Re-running the analysis
Run from the repository root (`rq2_analysis.py` imports `rq1_analysis.py`, so it must be run from here):
```bash
# RQ1 (M2) and Event A
python3 rq1_analysis.py -o rq1_results */m2_reproduction_results
python3 rq1_analysis.py -o event_a_analysis */event_a_results
# RQ2
python3 rq2_analysis.py -o rq2_results */m2_reproduction_results
python3 rq2_analysis.py -o event_a_analysis/rq2_event_a_results */event_a_results
# M4 annotation evidence (../../M4 holds project clones checked out at the M2 end SHAs; not in this repo)
python3 m4_annotation_analysis.py -o m4_annotation_results --clones ../../M4 \
  --scan ../../M4/maven-release ../../M4/slf4j ../../M4/jdbi ../../M4/jspwiki
# Audit checks
python3 verification/late_effect.py Jacks_Results/m2_reproduction_results/refactoringsFitnesse-2024.json verification/fitnesse_post_cutoff_commits.out
python3 verification/late_effect.py Jacks_Results/m2_reproduction_results/refactoringsControlBot-2024.json verification/connectbot_post_cutoff_commits.out
python3 verification/modifier_drivers.py */m2_reproduction_results/*.json
```
`rq1_analysis.py` mirrors the authors' `analyze/src/rq1_freq/analysis.py`: a refactoring is test code
if its left-side file path contains "test" (lowercased), and commits are labelled prod-only, test-only
or co-occurring. On 16 Nov 2026 every committed output in `rq1_results/`, `event_a_analysis/`,
`rq2_results/` and `m4_annotation_results/` was regenerated with the commands above and matched. The
only differences were the last floating-point digit of the standard-deviation column in the Event A
type tables, caused by a different Python version.

Run Maven test builds from a path **without spaces**: `PomFinderTest` in maven-release fails when the
path contains spaces (URL-encoded `%20`).

## Deviations from the frozen plan
1. **apache/pig** (row 8 of `DataCollection.csv`) exceeded the 3-hour RefactoringMiner limit and was replaced by **sgothel/jogl** (row 13), per the M1 rule. No run log was retained.
2. **fitnesse and connectbot** were mined to Dec 2024 instead of 1 Sep 2024. That adds 39 commits, of which 2 contain refactorings (3 prod + 1 test instance out of 202,102), so the ratio stays at 2.90× and the verdict is unchanged (`verification/late_effect_output.out`, `verification/end_commit_dates.out`).
3. **retrofit** (Event A) was mined from the `lysine-dev/retrofit` fork rather than `square/retrofit`.
4. **M4 module:** the M1 rule (top RQ2 module in a project that builds on JDK 17) would have selected junit4, since fitnesse fails to build on JDK 17. RQ1 showed that the main test-specific signal was test-framework annotation churn, not fixtures, so the design question changed to framework coupling. junit4 is the framework itself, so maven-release was chosen as the only candidate fully on JUnit 4 that builds on JDK 17 (`m4_annotation_results/junit_files.csv`, `verification/m4_candidate_builds/`).
5. **Event B verdict** was revised from "supported" to "partly supported": the frozen challenge condition "the upstream feature commit itself rewrites tests to JUnit 5" was met (`event_b/EVENT_B_PREDICTION.md`; upstream migrated in `c8d58e74`, 5 Nov 2025).

## Evidence added at FINAL
`m4/` holds only what was committed at `PRE_EVENT_B`. Everything added afterwards is in `verification/`,
so frozen and late-committed evidence stay separate:
- `verification/m4_candidate_builds/` contains the JDK 17 baseline builds of the other M4 candidates, run on 4 Nov 2026
  (before `PRE_EVENT_B`, 5 Nov) but not committed at the time. They support the M4 module choice:
  fitnesse fails to build on JDK 17, slf4j fails to compile, and junit4 builds (1,108 tests, 0 failures, 6 skipped).
- `verification/m4_alternative_trials/` contains the M4 alternatives trialled on 5 Nov 2026 (00:20–00:29, before the
  `PRE_EVENT_B` commit at 00:50) but not committed at the time. `vintage_change.diff` adds JUnit 5 + Vintage
  to maven-release; with it, all 740 existing tests still pass (Release Manager runs on the JUnit Platform
  provider). `maven-release_junit5_smoke.out` shows a JUnit 5 test running alongside them (the smoke test's
  source was not kept).
- `verification/jdk17_rerun/` (16 Nov 2026) re-runs the M4 baseline and Event B Response A with JDK 17
  set explicitly, because the original logs do not record the Java version (`env.out` records it).
  On OpenJDK 17.0.21 + Maven 3.9.16 from clean clones of `befc7786` (no spaces in path): baseline
  740 tests, 0 failures, 19 skipped; Response A (`event_b/response_A.diff` applied) 787 tests, 0 failures,
  19 skipped. Both match the original logs. `run.sh` is the script used.
- `verification/late_effect.py` and its outputs (16 Nov 2026) quantify the fitnesse/connectbot cut-off
  overrun (Deviation 2). The post-cut-off commit lists and end-commit dates come from the GitHub API.
- `verification/modifier_drivers.py` and its output (16 Nov 2026) show that the test-code
  ADD_PARAMETER_MODIFIER and ADD_VARIABLE_MODIFIER counts come mostly from bulk commits in jogl and jspwiki.

## Results summary
| | Paper | M2 (12 projects) | Event A (12 held-out) |
|---|---|---|---|
| Prod/test instance ratio | 4.67× | 2.90× | 3.73× |
| Instances prod/test | 82.4% / 17.6% | 74.3% / 25.7% | 78.8% / 21.2% |
| Commits prod/test/co-occur | 76.4 / 11.0 / 12.5% | 66.8 / 18.0 / 15.3% | 76.2 / 12.9 / 10.9% |
| Paper's top-5 test types in our top 5 | n/a | 3 of 5 | 3 of 5 |
| Verdict | n/a | Reproduced | Held |

- **RQ2:** the top 10% of production classes account for 52.7% of linked test refactorings, so the verdict is concentrated (5 of 12 projects concentrated).
- **M4:** no change (maven-release stays on JUnit 4; 740 tests, 0 failures, 19 skipped).
- **Event B:** the SemVer feature (upstream `5106eb19`) was ported with JUnit 4 tests (787 tests, 0 failures, 19 skipped). The M4 decision is partly supported.

## Limitations
- 12 projects against the paper's 455.
- The top-5 type match is exactly at the threshold, and it is shaped by bulk "add final" commits in jogl and jspwiki.
- The path-based test rule is inherited from the paper and can misclassify (for example junit4, fitnesse).
- The Foo/FooTest cross-check is weak in several projects (jogl 0%, openjpa 3.3%).
- The M4 module deviates from the M1 rule (Deviation 4).

## AI use (material contributions only)
- **Analysis scripts:** all analysis scripts (`rq1_analysis.py`, `rq2_analysis.py`, `m4_annotation_analysis.py`,
  and the `verification/` scripts) were created with AI. We checked `rq1_analysis.py` line by line against
  the authors' `analyze/src/rq1_freq/analysis.py`, and re-ran every script on the committed data to identical
  outputs before relying on them.
- **Event B JUnit builds:** AI was used to port upstream's JUnit 5 SemVer tests to JUnit 4 `Parameterized`
  (Response A) and to set up the JUnit 5 + Vintage build (Response B). Both were verified by running the
  tests: 49/49 in each response and the full build (787 tests, 0 failures), re-run on JDK 17 in
  `verification/jdk17_rerun/`. The diffs are kept in `event_b/response_A.diff` and `response_B.diff`.
- **Understanding the tasks:** AI was used to interpret the project brief, rubric and Event A/B task sheets
  and to work out what each stage required. We checked its reading against the documents themselves and
  the freeze rules before acting on it.
- **Fact checking and debate:** we used AI to challenge our own claims and its own answers, for example
  whether results met the frozen decision rules, whether the Event B verdict followed from our prediction,
  and whether the M4 module choice matched the M1 plan. Disagreements were settled against the data, logs
  and git history, not the AI's answer.
- **Final audit (16 Nov 2026):** an AI-assisted re-check against the authors' repo found the fitnesse/connectbot
  cut-off overrun, the narrowed Event B challenge condition, the deviation of the M4 module from the M1 rule
  and the missing JDK version in the build logs. Each was confirmed with the scripts and re-runs in
  `verification/` and the git history, then recorded as dated notes in the tracker.
- **AI output we corrected:** the audit itself made errors that verification caught. Its first re-run
  command for `m4_annotation_analysis.py` omitted the `--clones`/`--scan` options, so outputs did not match
  until fixed. It overstated one figure (97% instead of 96%). It also first stated "JDK 17" as fact before
  the logs were found not to record a Java version, which led to the explicit JDK 17 re-run.

## Team
G08 / P11: 
23364092 --> Ciarán Harris
23365277 --> Kai Howley
23366044 --> Oran Counihan
23372958 --> Jack Ryan
23388137 --> Eoin Stack
