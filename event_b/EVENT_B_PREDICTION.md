# Event B — prediction and feature-selection rule (written BEFORE any Event B analysis)

Written: 2026-11-10, before listing or inspecting any upstream commit after `befc7786`.
Pre-Event-B state: tag `PRE_EVENT_B` (`fe8f8ff`). M4 decision: no change — maven-release
stays on JUnit 4 (740 tests pass on JDK 17 @ `befc7786`).

## Feature
Smallest upstream feature (not bug fix) commit after `befc7786` that changes both production and
test code: `5106eb19` (2025-11-21) "Introduce new SemVer policies". Smaller prod+test commits
(`e2745edc`, `6d9e5e76`, `b5d5fb25`) are JIRA Bug fixes, so excluded.
(Feature chosen after this prediction was written; prediction text below is unchanged.)

## Prediction (draft for the group to confirm)
- **Affected part of the design:** the production classes the feature touches in
  `maven-release-manager` (or the module it lands in) and their existing JUnit 4 test classes.
- **Expected change surface:** test edits follow production edits in the same classes
  (signature/behaviour changes, the co-change types RQ2 found most often); few test files
  changed, no test-framework (annotation/import) changes needed.
- **Expected verdict:** the M4 no-change decision is **supported**.
- **What would challenge it:** the feature's tests need a JUnit 5-only capability (e.g.
  `@ParameterizedTest`, `@TempDir`, `assertThrows` beyond JUnit 4.13), the upstream feature
  commit itself rewrites tests to JUnit 5, or test edits spread well beyond the changed
  production classes.
