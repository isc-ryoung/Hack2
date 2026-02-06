# Implementation Plan: Instance - IRIS Operations Agent

**Branch**: `001-iris-ops-agent` | **Date**: 2026-02-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-iris-ops-agent/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The Instance project creates an **Agentic AI system** for simulating and remediating InterSystems IRIS database operational issues. The system has two primary capabilities:

1. **Error Simulation**: Generate realistic IRIS error messages based on patterns from actual messages.log files, covering configuration errors, license issues, OS resource constraints, and journal problems. Messages are transmitted to external monitoring systems.

2. **Intelligent Remediation**: Receive JSON remediation commands and execute appropriate actions through specialized agents (ConfigAgent for CPF changes, OSAgent for memory/CPU adjustments, RestartAgent for instance restarts). Agent selection and orchestration is LLM-powered for intelligent decision-making.

**Technical Approach**: Built using OpenAI Agents SDK for agent orchestration, with structured outputs using Pydantic models. Agents communicate via string-based interfaces within the same Python process. System emphasizes observability (structured logging with trace IDs), safety (validation and rollback), and educational value (notebook-driven development).

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
  
  FOR AGENTIC AI PROJECTS: Also specify LLM models, token budgets, agent types,
  and prompt management strategy.
-->

**Language/Version**: Python 3.10+ (for pattern matching, modern type hints, and dataclass features)  
**Primary Dependencies**: openai-agents-sdk, pydantic>=2.0, structlog, pytest, python-dotenv  
**LLM Models**: gpt-4o-2024-08-06 (for structured outputs), gpt-3.5-turbo (for cost-effective operations)  
**Storage**: JSON files for message queue persistence, file system for IRIS log samples and config files  
**Testing**: pytest with pytest-mock for LLM mocking, pytest-asyncio for async agent tests  
**Target Platform**: Jupyter/Colab notebooks for development and demos, Linux server for IRIS integration
**Project Type**: single project with notebook support (agents + simulation + workshop materials)  
**Performance Goals**: <5s LLM response p95, <10s end-to-end remediation for single-agent operations  
**Constraints**: <$0.50 per remediation workflow, <500 tokens per error generation, string-based inter-agent communication  
**Scale/Scope**: 20 workshop users, 5 agent types (ErrorGen, Orchestrator, Config, OS, Restart), 15 prompts  
**Token Budget**: 5K tokens per remediation workflow, 50K tokens per workshop session, 500K tokens/day for all users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with the Agentic AI Workshop Constitution:

- [x] **Agent-First Design**: Yes - 5 specialized agents (ErrorGenerator, OrchestratorAgent, ConfigAgent, OSAgent, RestartAgent), each with single responsibility, independent interfaces, and isolated testing
- [x] **Notebook-Driven**: Yes - Development starts in notebooks/ for exploration, agents prototyped in notebooks/experiments/, extracted to src/agents/ for production
- [x] **Test-Driven AI**: Yes - Tests defined in spec.md acceptance scenarios (30+ scenarios), unit tests for deterministic logic (validation, parsing), integration tests with mocked LLM responses, prompt regression tests
- [x] **Observability**: Yes - structlog for structured logging, trace IDs for correlation, all LLM calls logged with prompts/responses/tokens/latency, agent decision logging
- [x] **LLM Safety**: Yes - python-dotenv for API key management, retry logic with exponential backoff, 30s timeouts on LLM calls, fallback to rule-based processing, input validation
- [x] **Cost Management**: Yes - Token tracking per agent call, budget alerts at 80% threshold, prompt optimization (minimize context), caching for repeated error patterns, gpt-3.5-turbo for simple operations
- [x] **Educational Clarity**: Yes - Extensive docstrings with examples, notebooks/tutorials/ for step-by-step learning, inline comments explaining agent patterns, README with architecture diagrams

**Constitution Violations** (if any, must be justified in Complexity Tracking section):
- None - All constitutional principles satisfied

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
src/
├── agents/
│   ├── __init__.py
│   ├── error_generator.py      # ErrorGeneratorAgent - generates IRIS error messages
│   ├── orchestrator.py         # OrchestratorAgent - routes commands to agents
│   ├── config_agent.py         # ConfigAgent - modifies IRIS CPF files
│   ├── os_agent.py             # OSAgent - adjusts OS memory/CPU settings
│   └── restart_agent.py        # RestartAgent - manages IRIS restarts
├── models/
│   ├── __init__.py
│   ├── error_message.py        # ErrorMessage Pydantic model
│   ├── remediation_command.py  # RemediationCommand Pydantic model
│   ├── agent_responses.py      # Structured response models for each agent
│   └── execution_context.py    # ExecutionContext runtime state model
├── services/
│   ├── __init__.py
│   ├── log_parser.py           # Parse IRIS messages.log for patterns
│   ├── message_sender.py       # Send messages to external systems
│   ├── command_receiver.py     # Receive JSON commands from external systems
│   └── cpf_manager.py          # CPF file read/write/validation
├── prompts/
│   ├── __init__.py
│   ├── error_generation.py     # Prompt templates for error generation
│   ├── orchestration.py        # Prompt templates for agent selection
│   └── validation.py           # Prompt templates for pre/post validation
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Structured logging setup with trace IDs
│   ├── cost_tracker.py         # Token usage tracking and budget alerts
│   └── config.py               # Configuration management
└── __init__.py

notebooks/
├── demos/
│   ├── 01_error_generation_demo.ipynb
│   ├── 02_remediation_workflow_demo.ipynb
│   └── 03_agent_orchestration_demo.ipynb
├── experiments/
│   ├── log_pattern_analysis.ipynb
│   ├── agent_prototyping.ipynb
│   └── prompt_engineering.ipynb
└── tutorials/
    ├── 01_introduction_to_agents.ipynb
    ├── 02_building_custom_agents.ipynb
    └── 03_agent_testing_patterns.ipynb

tests/
├── unit/
│   ├── test_log_parser.py
│   ├── test_cpf_manager.py
│   ├── test_error_message_model.py
│   └── test_command_validation.py
├── integration/
│   ├── test_error_generator_agent.py      # With mocked LLM
│   ├── test_orchestrator_agent.py         # With mocked LLM
│   ├── test_config_agent.py               # With mocked file system
│   └── test_end_to_end_workflow.py        # Full workflow with mocks
├── prompts/
│   ├── test_error_prompts.py              # Prompt regression tests
│   └── test_orchestration_prompts.py
└── fixtures/
    ├── sample_messages.log                # Test log samples
    ├── sample_iris.cpf                    # Test CPF files
    └── sample_commands.json               # Test remediation commands

log_samples/                   # Existing directory with messages.log

specs/
└── 001-iris-ops-agent/
    ├── spec.md
    ├── plan.md                # This file
    ├── research.md            # Phase 0 output (to be created)
    ├── data-model.md          # Phase 1 output (to be created)
    ├── quickstart.md          # Phase 1 output (to be created)
    ├── contracts/             # Phase 1 output (to be created)
    │   ├── error_message_schema.json
    │   ├── remediation_command_schema.json
    │   └── agent_response_schemas.json
    └── checklists/
        └── requirements.md
```

**Structure Decision**: Selected **Single Project** structure with notebook support. This is appropriate because:
- All agents operate within same Python process with string-based communication (no microservices)
- Educational/workshop focus benefits from unified codebase
- Notebook-driven development aligns with single project layout
- No frontend UI required (pure agent system)
- Simplified testing and deployment for workshop scenarios

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
