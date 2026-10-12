# AI Activity Log — Week 01

**Project:** EnglishGo — AI Visual Vocabulary Learning
**Course:** Software Engineering (INFO2005)
**Development direction:** Upgrade Existing Project
**AI Agent:** OpenAI Codex CLI 0.162.1
**Status:** In Progress

## Activity 01 — Repository Onboarding

**Task:** Analyze the original AI-English repository.

**Objective:** Understand the existing application before planning the EnglishGo upgrade.

### Prompt

Analyze the existing AI-English repository.

Identify:

1. Application entry point.
2. Main modules and their responsibilities.
3. Current Python GUI framework.
4. AI/ML components.
5. Database access mechanism.
6. Existing automated tests.

Constraints:

- Read-only analysis.
- Do not modify or create files.
- Do not execute database migrations.
- Do not access or display `.env` values.
- Do not commit or push changes.
- Provide relevant source file paths.

### AI Output Summary

Codex reported:

- Entry point: `main.py`, launching `ui.main_qt.run()`.
- GUI: PySide6 with Qt Quick/QML.
- AI: YOLO detection, vocabulary mapping and AI pipeline.
- Machine learning: k-NN recommendation and K-Means clustering.
- Database: PostgreSQL using psycopg2 and a threaded connection pool.
- Data access: SQL repositories and dataclass entities.
- Testing: Approximately 392 test methods identified through static inspection across 13 modules.

### Human Review

The student compared the output against the project's README and previously inspected source files.

Accepted findings:

- Application entry point and core technology stack.
- Existing Python desktop architecture.
- Main AI/ML and database responsibilities.
- Need to evaluate reusable modules before migrating to a web application.

Not yet verified:

- Whether all reported tests are collected successfully.
- Whether the entire application runs correctly.
- Whether all current AI model files load successfully.
- Whether existing modules can be reused without modification in a web backend.

### Execution Issue

During initial repository inspection, Codex encountered an execution-environment initialization error (`helper_unknown_error`). The subsequent repository-analysis report was obtained, but successful automated test execution has not been demonstrated.

### Decision

Accept the AI output as a preliminary codebase analysis.

Do not begin rewriting the desktop application or migrating the database until the requirements and architecture are reviewed.

### Testing

- PostgreSQL/Supabase connection: Previously tested successfully.
- Automated test suite: Not executed as part of this recorded activity.
- Application UI smoke test: Not yet confirmed.

### Files Changed

No source-code modification was requested from Codex during the read-only analysis.

---

## Week 01 Reflection

AI assistance helped identify the application modules and current architecture more quickly.

Human review remains necessary to verify technical claims, especially test counts, actual runtime behavior, and upgrade feasibility.

**Next actions:** Complete the AI usage policy, review Week 01 documentation, validate Git changes, and prepare the Week 01 commit.

## Activity 02 — Flaky Test Investigation and Stabilization

**Project:** EnglishGo — Upgrade AI-English
**Tool:** Codex CLI 0.162.1
**Task:** Stabilize cancellation lifecycle test.

### Problem

The original regression suite contained an intermittent failure in:

`test/test_cancellation.py::ManagedWorkerLifecycleTest::test_cancel_mid_run_ends_in_cancelled`

Observed error:

`AssertionError: Lists differ: [] != [1]`

### Reproduction

The isolated test was executed 10 times before the fix.

- Passed: 8
- Failed: 2

This established that the test was flaky.

### AI-Assisted Investigation

Codex inspected the worker lifecycle, Qt event-processing helper, and test implementation.

The likely cause was a timing issue between the worker reaching the `CANCELLED` state and the `cancelled` signal callback executing.

### Implementation

The test was updated to wait for both the expected worker state and the cancelled signal.

The final assertion still verifies that the signal was observed exactly once.

Codex also removed one duplicate assertion detected in the working tree.

### Verification

Codex reported 30 successful targeted test runs.

Independent student verification:

- Targeted tests: 10 passed, 0 failed.
- Full regression suite: Completed successfully, exit code 0.
- Previously collected tests: 392.
- No failures appeared in the final full-suite output.

### Human Review

The student reproduced the original failure, reviewed the proposed test-side synchronization approach, and independently executed the targeted and full regression tests.

**Decision:** Accept the fix for the Week 01 baseline, subject to final Git diff review.

**Remaining limitation:** Timing-related behavior should continue to be monitored in CI and future regression runs.

## Activity 03 — Worker Finished Signal Timing Investigation

**Project:** EnglishGo — Upgrade AI-English
**Task:** Stabilize the worker finished-state test.

### Problem

A full regression run intermittently failed at:

`test/test_cancellation.py::ManagedWorkerLifecycleTest::test_successful_run_ends_in_finished`

**Observed failure:** The worker reached the `FINISHED` state, but the `"finished"` signal had not yet been observed by the test.

### Analysis

Inspection of `ManagedWorker._set_state()` showed that the internal state is updated before `stateChanged` is emitted.

The test previously waited for the internal state only and then immediately checked the signal list.

This creates a possible timing issue between worker state changes and Qt signal delivery.

### Implementation

The test was adjusted to wait until both conditions were satisfied:

- Worker state equals `FINISHED`.
- The `"finished"` state signal has been received.

The previously fixed cancellation test was also cleaned up by removing duplicate assertions and restoring an accidentally modified comment.

### Verification

- Full pytest suite completed with exit code `0`.
- Previously collected test count: 392.
- `git diff --check` reported no errors.
- Final diff was reviewed to confirm the intended changes were limited to test synchronization.

### Human Review

The student checked the test implementation, corrected unintended changes, ran pytest independently, and inspected the final Git diff.

**Decision:** Accept the test synchronization changes for the Week 01 baseline.

**Remaining risk:** Qt timing-sensitive tests should continue to be monitored in future CI runs.