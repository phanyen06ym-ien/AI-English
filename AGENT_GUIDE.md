# AGENT_GUIDE — EnglishGo

**Project:** EnglishGo — AI Visual Vocabulary Learning
**Development direction:** Upgrade Existing Project
**Original repository:** https://github.com/phanyen06ym-ien/AI-English
**Status:** Week 01 — Draft

## 1. Project Context

EnglishGo is an AI-assisted English vocabulary learning web application developed by upgrading the existing AI-English desktop project.

The original project uses Python 3.11, PySide6/QML, YOLO, k-NN, K-Means, and PostgreSQL.

The target product will support image-based vocabulary discovery, personal vocabulary collections, quizzes, and learning history.

Proposed features must not be treated as already implemented.

## 2. Agent Responsibilities

The AI Agent may assist with:

- Repository analysis and code navigation.
- Implementation planning.
- Code changes within approved scope.
- Unit test generation and execution.
- Documentation and technical explanations.
- Code review and identifying potential risks.

The student remains responsible for checking, approving, and integrating changes.

## 3. Required Workflow

**Analyze → Plan → Implement → Test → Human Review**

1. Analyze: Read the relevant files and identify dependencies.
2. Plan: Explain proposed changes, impacted modules, risks, and tests.
3. Implement: Modify only files within the approved task scope.
4. Test: Run relevant tests and report actual results.
5. Human Review: Present the diff, limitations, and unresolved issues for student approval.

Do not claim tests passed unless they were executed.

## 4. Repository Rules

- Do not develop directly on `main`.
- Use a task-specific Git branch.
- Do not commit or push without explicit approval.
- Do not overwrite unrelated changes.
- Never commit `.env`, credentials, tokens, or private information.
- Keep `.env.example` free of real secrets.
- Preserve existing application behavior unless changes are approved.
- Do not delete legacy modules without demonstrating why they can be replaced.

## 5. Database Rules

- Database: PostgreSQL hosted on Supabase.
- Existing access mechanism: psycopg2 and typed dataclass entities.
- ORM migration is not yet approved.
- Do not create, alter, or delete production database tables without approval.
- Do not execute destructive SQL automatically.
- Prefer explicit database migrations and reviewable schema changes.

## 6. AI Feature Rules

- Treat object-detection results as predictions, not verified facts.
- Handle unsupported labels and low-confidence results.
- Preserve user control over vocabulary selection.
- Avoid retaining raw images by default.
- Do not send images or personal information to external providers without an approved data-processing flow.

## 7. Testing Requirements

- Identify existing tests before making changes.
- Add tests for new business rules.
- Run relevant automated tests after changes.
- Report failures accurately.
- Verify authentication, ownership, input validation, and privacy-sensitive operations where applicable.

## 8. Documentation and AI Logs

Record meaningful AI-assisted development activities in `ai-logs/week-XX.md`.

Each log should include:

- Date and task.
- Agent/tool used.
- Prompt or prompt reference.
- Summary of AI output.
- Student verification.
- Accepted or rejected changes.
- Tests performed and their actual results.

Do not fabricate prompts, test results, commits, or reviews.

## 9. Decision Authority

The AI Agent may recommend technical solutions, but the student must approve architecture decisions, scope changes, database modifications, security-related changes, and commits.

**Primary principle:** AI assists software engineering; human review remains mandatory.