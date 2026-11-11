# Event B — results (maven-release, from PRE_EVENT_B state `befc7786`, JUnit 4)

Feature: upstream `5106eb19` "Introduce new SemVer policies" (5 new SemVer version policies, shared
base class `AbstarctSemVerVersionPolicy`, `SemVerVersionPolicy` deprecated and made a subclass of
`SemVerMinorDevelopmentVersionPolicy`). Ported to `befc7786` by copying upstream's 7 production files
unchanged (a direct cherry-pick conflicts with intervening upstream commits, incl. the JUnit 5
migration `c8d58e74`). Docs/site/IT-groovy and Mojo javadoc edits not ported (no behaviour).

Upstream wrote the 6 test classes in JUnit 5 (`@ParameterizedTest` + `@CsvSource`, 49 cases).

## Responses compared
| | A: no structural change (JUnit 4) | B: add JUnit 5 + Vintage to the module |
|---|---|---|
| Production files | 7 (+305/-32), identical in A and B | same |
| Test files | 6 (+399/-18): upstream cases rewritten as JUnit 4 `@RunWith(Parameterized.class)` | 6 (+346/-10): upstream tests verbatim |
| Build files | 0 | 1 (`maven-release-semver-policy/pom.xml`, +18) |
| Test cases | 49 (all upstream cases, counted per file) | 49 |
| SemVer module runner | JUnit4Provider | JUnitPlatformProvider |
| SemVer module tests | 49 run, 0 fail (`A_junit4_semver.out`) | 49 run, 0 fail (`B_junit5_semver.out`) |
| Full build | 787 run, 0 fail, 19 skipped, all 6 modules SUCCESS (`A_full_build.out`) | module only |
| JUnit 4 test files in repo | 59 -> 64 | 59 -> 58 (+6 JUnit 5) |

Baseline (frozen): SemVer module 2 tests, JUnit4Provider (`A0_baseline_semver.out`); full build 740
tests (M4 evidence).

Diffs: `response_A.diff`, `response_B.diff`; per-file counts: `surface_A.tsv`, `surface_B.tsv`.

## Chosen response: A (no structural change)

## Observations
- Change surface is proportional and local: all edits are in the SemVer module; test edits follow
  the new production classes one-to-one (6 test classes for 5 new policies + the changed one).
- Production-style refactoring -> test-design problem: production extracted a shared base class
  (`AbstarctSemVerVersionPolicy`), but the tests did not; 6 near-identical test classes differ only in
  their data. This duplication exists in upstream's JUnit 5 version and in our JUnit 4 port.
- JUnit 4 cost: `Parameterized` allows one data set per class, so each upstream class's two
  parameterised methods were merged into one method with a `kind` column (72 vs 65 lines for
  SemVerMinorReleaseVersionPolicyTest). Expressible, slightly clunkier.
- A adds 5 JUnit 4 files (59 -> 64), i.e. more future migration work.
