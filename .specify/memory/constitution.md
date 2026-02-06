<!--
SYNC IMPACT REPORT - Constitution v1.0.0
═══════════════════════════════════════════════════════════════════

VERSION: Initial → 1.0.0 (MINOR - Initial constitution creation)

CREATED SECTIONS:
  ✓ Core Principles (7 principles defined)
  ✓ Technical Standards
  ✓ Development Workflow
  ✓ Governance

PRINCIPLES DEFINED:
  1. Agent-First Design
  2. Notebook-Driven Development
  3. Test-Driven AI Development (NON-NEGOTIABLE)
  4. Observability & Debugging
  5. LLM Integration Safety
  6. Cost Management
  7. Educational Clarity

TEMPLATES STATUS:
  ✅ .specify/templates/plan-template.md - Updated with AI-specific constitution checks
     - Added concrete checklist for 7 principles
     - Added LLM models, token budget, AI-specific performance goals
     - Updated source structure with agents/, prompts/, notebooks/ directories
  ✅ .specify/templates/spec-template.md - Updated with AI-specific success criteria
     - Added AI-specific success criteria section (quality, latency, cost, education metrics)
  ✅ .specify/templates/tasks-template.md - Updated with AI-specific task patterns
     - Added foundational AI infrastructure tasks (LLM client, logging, prompt management)
     - Added AI-specific test types (prompt regression, mock LLM, real LLM tests)
     - Added agent implementation task patterns (observability, cost tracking, notebook extraction)
  ✅ .specify/templates/checklist-template.md - No changes required (generic checklist)
  ✅ .specify/templates/agent-file-template.md - No changes required (agent-agnostic template)

FOLLOW-UP TODOS: None

RECOMMENDED PROJECT STRUCTURE:
Based on the constitution, the recommended structure for this Agentic AI project is:
```
src/
  agents/          # Each agent = one file
  models/          # Data schemas
  services/        # LLM integration layer
  prompts/         # Prompt templates
  utils/           # Logging, tracing, cost tracking
notebooks/
  demos/           # Workshop demos
  experiments/     # Development notebooks
  tutorials/       # Educational content
tests/
  unit/            # Deterministic logic tests
  integration/     # Mock LLM tests
  prompts/         # Prompt regression tests
```

COMMIT MESSAGE SUGGESTION:
docs: create Agentic AI Workshop constitution v1.0.0

- Define 7 core principles for AI agent development
- Establish test-driven, notebook-first, observable AI workflow
- Update templates with AI-specific guidelines
- Add cost management, LLM safety, and educational clarity standards
═══════════════════════════════════════════════════════════════════
-->

# Agentic AI Workshop Constitution

## Core Principles

### I. Agent-First Design

Every AI system must be designed as composable agents with clear responsibilities:
- **Single Responsibility**: Each agent handles one specific domain or capability
- **Modularity**: Agents must be independently testable and reusable
- **Clear Interfaces**: Agent inputs/outputs must be well-defined with schemas
- **Stateless Preferred**: Agents should be stateless when possible; state management must be explicit
- **Error Boundaries**: Each agent must handle its own errors gracefully with fallback strategies

**Rationale**: Agentic systems become unmaintainable without clear boundaries. Modularity enables testing, debugging, and iterative development essential for AI systems where behavior is non-deterministic.

### II. Notebook-Driven Development

Development prioritizes interactive notebooks for exploration and education:
- **Notebooks as Primary Environment**: Core development happens in Jupyter notebooks first
- **Cell Independence**: Each notebook cell must be executable independently (after dependencies)
- **Educational Structure**: Code must include markdown explanations suitable for workshop participants
- **Export Path**: Production code must be extractable to `.py` modules without loss of functionality
- **Version Control**: Notebooks committed with outputs cleared; use `.ipynb` properly in git

**Rationale**: Workshops require interactive learning environments. Notebooks enable experimentation, visualization, and stepwise refinement critical for AI development and teaching.

### III. Test-Driven AI Development (NON-NEGOTIABLE)

All agent logic and integrations must follow TDD principles adapted for AI:
- **Test-First Workflow**: Write tests → Tests fail → Implement → Tests pass → Refactor
- **Unit Tests for Logic**: Deterministic agent logic (parsing, routing, validation) must have unit tests
- **Integration Tests for LLM**: Mock LLM responses for integration tests; separate tests for actual API calls
- **Prompt Testing**: Critical prompts must have regression tests with expected outputs
- **Evaluation Metrics**: Define success criteria (accuracy, latency, cost) before implementation
- **User Acceptance**: Tests derived from user stories must pass before feature is complete

**Rationale**: AI systems are probabilistic and hard to debug. Without tests, regressions are invisible, costs explode, and reliability suffers. TDD forces clarity about expected behavior upfront.

### IV. Observability & Debugging

All agent interactions and LLM calls must be traceable and debuggable:
- **Structured Logging**: Use structured logs (JSON) for all agent actions, decisions, and LLM calls
- **Trace IDs**: Each agent execution flow must have a unique trace ID for end-to-end tracking
- **LLM Interaction Logging**: Log prompts, responses, token usage, latency for every LLM call
- **Decision Transparency**: Agents must log WHY they made decisions (reasoning traces)
- **Replay Capability**: System must support replaying agent flows from logs for debugging
- **Log Sampling**: Production logs should support sampling to avoid storage bloat

**Rationale**: AI systems fail in opaque ways. Without comprehensive logging, debugging user-reported issues is impossible, and understanding model behavior is guesswork.

### V. LLM Integration Safety

All interactions with LLM APIs must follow safety and reliability practices:
- **API Key Security**: Never hardcode API keys; use environment variables or secret management
- **Error Handling**: Handle rate limits, timeouts, API errors with exponential backoff and retries
- **Rate Limiting**: Implement client-side rate limiting to prevent API quota exhaustion
- **Timeout Controls**: All LLM calls must have explicit timeouts (default: 30s)
- **Content Filtering**: Implement input/output filtering for harmful content where applicable
- **Fallback Strategies**: Define fallback behavior when LLM calls fail (cached responses, simpler models)
- **Model Versioning**: Pin model versions in code; document upgrade path when models change

**Rationale**: LLM APIs are external services with variable reliability. Without defensive programming, systems fail unpredictably. Security lapses expose API keys and user data.

### VI. Cost Management

LLM usage must be monitored and optimized to prevent budget overruns:
- **Token Usage Tracking**: Log input/output tokens for every LLM call; aggregate in metrics
- **Cost Budgets**: Define per-feature or per-user cost budgets; alert when exceeded
- **Prompt Optimization**: Minimize token usage through prompt engineering and context pruning
- **Caching Strategy**: Cache repeated LLM requests with TTL to reduce redundant API calls
- **Model Selection**: Use smallest capable model for each task (GPT-4 vs GPT-3.5 vs fine-tuned)
- **Batch Processing**: Batch independent LLM calls when possible to amortize latency costs

**Rationale**: LLM costs scale non-linearly with usage. Unmonitored systems can burn thousands of dollars in hours. Optimization is impossible without measurement.

### VII. Educational Clarity

All code and documentation must be accessible to workshop participants:
- **Code Readability**: Prioritize readability over cleverness; favor explicit over implicit
- **Inline Documentation**: Every complex function/agent must have docstrings with examples
- **Progressive Complexity**: Start simple, add complexity incrementally; mark advanced sections
- **Error Messages**: Error messages must be helpful and actionable, not cryptic stack traces
- **Workshop-Ready**: Code must run in notebook environments (Colab, Jupyter) without complex setup
- **Commented Examples**: Provide commented example usage for every major component

**Rationale**: This is an educational project. If participants cannot understand and extend the code, the workshop fails. Clarity is non-negotiable.

## Technical Standards

**Language & Runtime**:
- Python 3.10+ (required for modern type hints and pattern matching)
- Jupyter Notebook / JupyterLab 4.0+ or Google Colab compatibility
- Virtual environment required (venv, conda, or poetry)

**Core Dependencies**:
- `openai` (LLM API client)
- `pytest` (testing framework)
- `python-dotenv` (environment variable management)
- `structlog` or `loguru` (structured logging)
- Type hints mandatory for all public interfaces

**Code Quality**:
- Formatting: `black` (line length 100)
- Linting: `ruff` or `flake8` with type checking via `mypy`
- Import sorting: `isort`
- Pre-commit hooks for formatting/linting checks

**Storage & State**:
- Prefer stateless agents where possible
- Use JSON files for simple persistence in workshops
- SQLite for relational data if needed (avoid external DB dependencies)
- Document state schema explicitly

**Performance Targets**:
- LLM calls: <5s p95 latency (excluding model processing time)
- Agent execution: <10s p95 end-to-end for typical workflows
- Notebook cells: <30s execution time (flag slower cells with warnings)

## Development Workflow

**Feature Development Process**:
1. **Spec First**: Define user stories and acceptance criteria in `/specs/[feature]/spec.md`
2. **Design**: Create data models, agent contracts, and interaction flows
3. **Test Creation**: Write failing tests for user stories (unit + integration)
4. **Implementation**: Develop in notebooks, incrementally making tests pass
5. **Extraction**: Move production code to `.py` modules; keep notebooks as demos
6. **Validation**: Run full test suite, verify cost/performance metrics
7. **Documentation**: Update workshop materials and inline documentation

**Constitution Compliance**:
- All PRs/commits must reference which principles they satisfy
- Constitution violations must be explicitly documented and justified in `/specs/[feature]/plan.md`
- Automated checks for API key exposure, missing tests, and code quality

**Task Organization**:
- Tasks grouped by user story (US1, US2, ...) for independent delivery
- Parallel tasks marked with `[P]` to enable concurrent work
- Tests marked as `[T]` to distinguish from implementation tasks

**Review Gates**:
- Self-review: Run tests, check logs, verify cost metrics before commit
- Peer review: At least one workshop collaborator reviews for clarity
- Integration check: Verify notebook runs end-to-end in clean environment

## Governance

**Constitutional Authority**:
This constitution supersedes all other development practices. In conflicts between this document and existing code/docs, the constitution takes precedence. Amendments require:
1. Documented rationale for change
2. Impact analysis on existing specs, templates, and code
3. Migration plan if breaking changes introduced
4. Version bump following semantic versioning rules

**Version Semantics**:
- **MAJOR**: Removal of principles, backward-incompatible governance changes
- **MINOR**: New principles added, materialy expanded guidance, new sections
- **PATCH**: Clarifications, wording improvements, non-semantic fixes

**Amendment Process**:
1. Propose change with reasoning in constitution file as comment
2. Review impact on `.specify/templates/` and existing specs
3. Update constitution with new version and sync report
4. Propagate changes to affected templates and documentation
5. Announce to workshop participants if principles change

**Compliance Review**:
- Monthly review of recent features against principles
- Track principle violations and justifications
- Identify patterns requiring principle updates or training

**Enforcement**:
- Automated pre-commit checks for code quality, test coverage, API key exposure
- Mandatory Constitution Check in `/specs/[feature]/plan.md` before implementation
- Workshop facilitators verify adherence during code review sessions

**Version**: 1.0.0 | **Ratified**: 2026-02-06 | **Last Amended**: 2026-02-06
