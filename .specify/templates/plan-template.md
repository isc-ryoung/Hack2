# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
  
  FOR AGENTIC AI PROJECTS: Also specify LLM models, token budgets, agent types,
  and prompt management strategy.
-->

**Language/Version**: [e.g., Python 3.10+, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., openai, fastapi, pytest, structlog or NEEDS CLARIFICATION]  
**LLM Models**: [e.g., gpt-4o, gpt-3.5-turbo with version pins or N/A]  
**Storage**: [if applicable, e.g., SQLite, JSON files, PostgreSQL or N/A]  
**Testing**: [e.g., pytest with mocked LLM responses or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Jupyter/Colab notebooks, Linux server, cloud functions or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile/notebook - determines source structure]  
**Performance Goals**: [e.g., <5s LLM response p95, <10s agent execution or NEEDS CLARIFICATION]  
**Constraints**: [e.g., <$0.10 per user session, offline-capable agents or NEEDS CLARIFICATION]  
**Scale/Scope**: [e.g., 100 workshop users, 5 agent types, 20 prompts or NEEDS CLARIFICATION]  
**Token Budget**: [e.g., 10K tokens/session, 100K tokens/day or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with the Agentic AI Workshop Constitution:

- [ ] **Agent-First Design**: Are agents single-responsibility and independently testable?
- [ ] **Notebook-Driven**: Does development start in notebooks with educational structure?
- [ ] **Test-Driven AI**: Are tests defined upfront (unit tests for logic, integration for LLM)?
- [ ] **Observability**: Are LLM calls logged with prompts, responses, tokens, and trace IDs?
- [ ] **LLM Safety**: Are API keys secured, errors handled, timeouts set, and fallbacks defined?
- [ ] **Cost Management**: Is token usage tracked, cached, and optimized per the budget?
- [ ] **Educational Clarity**: Is code readable with docstrings, examples, and workshop-ready?

**Constitution Violations** (if any, must be justified in Complexity Tracking section):
- None / [List violations with justification]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── agents/          # Agent implementations (each agent = one file)
├── models/          # Data models and schemas
├── services/        # Business logic and LLM integrations
├── prompts/         # Prompt templates and management
├── cli/             # Command-line interfaces (if applicable)
└── utils/           # Logging, tracing, cost tracking utilities

notebooks/           # Development and workshop notebooks
├── demos/           # Demo notebooks for workshop participants
├── experiments/     # Exploration and testing notebooks
└── tutorials/       # Step-by-step tutorial notebooks

tests/
├── contract/        # Agent contract tests
├── integration/     # LLM integration tests (mocked + real)
├── unit/            # Unit tests for deterministic logic
└── prompts/         # Prompt regression tests

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── agents/      # Agent implementations
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
