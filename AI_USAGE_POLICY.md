# AI_USAGE_POLICY — EnglishGo

**Project:** EnglishGo — AI Visual Vocabulary Learning
**Course:** Software Engineering (INFO2005)
**Development Direction:** Upgrade Existing Project
**Status:** Week 01 — Draft

## 1. Purpose

This policy defines how AI coding agents and generative AI tools are used in the EnglishGo software engineering project.

AI tools assist development, but students remain accountable for technical decisions, academic integrity, security, and delivered software quality.

## 2. Permitted AI Usage

AI tools may assist with:

- Analyzing and explaining the existing AI-English codebase.
- Identifying defects and technical risks.
- Proposing software architecture and implementation plans.
- Generating or refactoring code within approved scope.
- Creating unit tests and reviewing test results.
- Reviewing Git diffs and suggesting improvements.
- Drafting technical documentation and development logs.

All generated outputs require human verification before acceptance.

## 3. Human Review Process

Every AI-assisted implementation must follow:

**Analyze → Plan → Implement → Test → Human Review**

Before accepting changes, students must:

1. Understand the purpose and behavior of modified code.
2. Review the Git diff and identify unrelated changes.
3. Run relevant automated and manual tests.
4. Verify security, privacy, and compatibility requirements.
5. Document accepted changes, rejected suggestions, and unresolved risks.

AI-generated code must never be accepted solely because the agent claims it works.

## 4. Restricted Actions

AI agents must not:

- Read, reveal, or commit secrets, API keys, credentials, or `.env` values.
- Commit, push, merge, or delete branches without explicit approval.
- Execute destructive database operations without authorization.
- Modify unrelated files outside the approved task.
- Upload private user images or sensitive information to unapproved services.
- Fabricate testing outcomes, prompts, activity logs, or development evidence.

## 5. AI Feature Safety

EnglishGo uses AI-based object recognition for vocabulary learning.

The application must treat model outputs as predictions, not verified facts.

Required principles:

- Allow users to review AI recognition results.
- Handle unsupported and incorrect labels.
- Validate vocabulary against curated data.
- Avoid retaining uploaded images by default.
- Require appropriate confirmation before sending images to external AI providers.
- Communicate errors and uncertainty appropriately.

## 6. Data Protection

- Keep Supabase credentials outside Git.
- Use `.env.example` only for placeholder configuration.
- Avoid sending personal data to development AI tools.
- Apply access control to personal vocabulary and Quiz history.
- Review storage, deletion, and retention behavior before deployment.

## 7. AI Activity Logs

Record meaningful AI-assisted development in `ai-logs/week-XX.md`.

Each record must identify:

- Date and task.
- Tool and prompt.
- AI-generated output.
- Human review and decision.
- Changes made.
- Tests executed and actual outcomes.

Failed experiments should also be documented.

## 8. Academic Integrity

All team members must be able to explain the software's requirements, architecture, implementation, and testing.

AI assistance must not replace the student's understanding or responsibility.

## 9. Policy Maintenance

Review this document when the project changes its architecture, AI provider, data-processing approach, or development workflow.

**Principle:** AI assistance is permitted; human accountability is mandatory.