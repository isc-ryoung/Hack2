# Tasks: Instance - IRIS Operations Agent

**Input**: Design documents from `/specs/001-iris-ops-agent/`  
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

**Branch**: `001-iris-ops-agent`  
**Generated**: 2026-02-06

**Tests**: Constitution mandates Test-Driven AI - tests are included for all user stories

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure (src/, tests/, notebooks/, specs/, log_samples/)
- [ ] T002 Initialize Python 3.10+ project with pyproject.toml or requirements.txt
- [ ] T003 [P] Add dependencies: openai-agents-sdk, pydantic>=2.0, structlog, pytest, pytest-mock, pytest-asyncio, python-dotenv
- [ ] T004 [P] Configure .env.example with API key placeholders, model settings, token budgets
- [ ] T005 [P] Setup .gitignore for Python (.venv/, __pycache__/, .env, *.pyc)
- [ ] T006 [P] Create README.md with project overview, installation instructions, and quickstart
- [ ] T007 [P] Configure pytest.ini with test paths and markers

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Foundational Infrastructure

- [ ] T008 [P] Implement structured logging setup with structlog in src/utils/logger.py
- [ ] T009 [P] Create trace ID context management using contextvars in src/utils/logger.py
- [ ] T010 [P] Implement cost tracking utilities (token counting, budget alerts) in src/utils/cost_tracker.py
- [ ] T011 [P] Create configuration management from .env in src/utils/config.py
- [ ] T012 Setup OpenAI client wrapper with API key management, retries, timeouts in src/utils/llm_client.py
- [ ] T013 [P] Create base Agent class with observability hooks in src/agents/base_agent.py
- [ ] T014 [P] Implement prompt template management system in src/prompts/__init__.py

### Foundational Data Models

- [ ] T015 [P] Create ErrorMessage Pydantic model in src/models/error_message.py
- [ ] T016 [P] Create RemediationCommand Pydantic model in src/models/remediation_command.py
- [ ] T017 [P] Create ExecutionContext model for runtime state in src/models/execution_context.py
- [ ] T018 [P] Create agent response models (OrchestratorResponse, ConfigAgentResponse, OSAgentResponse, RestartAgentResponse) in src/models/agent_responses.py

### Foundational Services

- [ ] T019 [P] Implement log parser service to extract patterns from log_samples/messages.log in src/services/log_parser.py
- [ ] T020 [P] Implement CPF file manager with configparser in src/services/cpf_manager.py

### Foundational Tests

- [ ] T021 [P] Unit test for logger setup and trace ID propagation in tests/unit/test_logger.py
- [ ] T022 [P] Unit test for cost tracker with token counting in tests/unit/test_cost_tracker.py
- [ ] T023 [P] Unit test for ErrorMessage model validation in tests/unit/test_error_message_model.py
- [ ] T024 [P] Unit test for RemediationCommand model validation in tests/unit/test_remediation_command_model.py
- [ ] T025 [P] Unit test for log parser with sample log file in tests/unit/test_log_parser.py
- [ ] T026 [P] Unit test for CPF manager read/write operations in tests/unit/test_cpf_manager.py
- [ ] T027 [P] Create test fixtures directory with sample files (tests/fixtures/sample_messages.log, sample_iris.cpf, sample_commands.json)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Error Message Generation (Priority: P1) 🎯 MVP

**Goal**: Generate realistic IRIS error messages based on patterns from messages.log, covering configuration, license, OS resource, and journal errors

**Independent Test**: Trigger error generation for each category (config, license, OS, journal) and verify output matches IRIS message.log format with correct timestamp, process ID, severity, category, and message text

### Tests for User Story 1

**Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T028 [P] [US1] Unit test for error pattern extraction from log samples in tests/unit/test_error_pattern_extraction.py
- [ ] T029 [P] [US1] Unit test for ErrorGenerationRequest model in tests/unit/test_error_generation_request.py
- [ ] T030 [P] [US1] Mock LLM test for error generation with fixed responses in tests/integration/test_error_generator_agent.py
- [ ] T031 [P] [US1] Prompt regression test for error generation prompts in tests/prompts/test_error_prompts.py
- [ ] T032 [US1] Integration test for all error categories (config, license, OS, journal) in tests/integration/test_error_generation_workflow.py

### Implementation for User Story 1

- [ ] T033 [P] [US1] Create ErrorGenerationRequest model in src/models/error_message.py
- [ ] T034 [P] [US1] Design prompt templates for error generation (config, license, OS, journal) in src/prompts/error_generation.py
- [ ] T035 [US1] Implement log pattern extraction on startup in src/services/log_parser.py (load and cache patterns)
- [ ] T036 [US1] Implement ErrorGeneratorAgent with LLM integration in src/agents/error_generator.py
- [ ] T037 [US1] Add structured output parsing using Pydantic response_format in src/agents/error_generator.py
- [ ] T038 [US1] Add observability (trace IDs, token tracking, pattern logging) to ErrorGeneratorAgent
- [ ] T039 [US1] Add cost tracking and budget alerts for error generation
- [ ] T040 [US1] Implement fallback to regex templates when LLM unavailable in src/agents/error_generator.py
- [ ] T041 [P] [US1] Create workshop notebook demonstrating error generation in notebooks/demos/01_error_generation_demo.ipynb

**Checkpoint**: User Story 1 fully functional - can generate realistic IRIS errors independently

---

## Phase 4: User Story 2 - External Message Output (Priority: P2)

**Goal**: Send generated error messages to external consumer system through configured interface

**Independent Test**: Generate error messages and verify they are transmitted to configured endpoint with delivery confirmation. Test with unavailable endpoint to verify queueing/error handling

### Tests for User Story 2

- [ ] T042 [P] [US2] Unit test for message formatting (JSON output) in tests/unit/test_message_sender.py
- [ ] T043 [P] [US2] Mock external endpoint test for successful transmission in tests/integration/test_message_sender.py
- [ ] T044 [P] [US2] Integration test for message queue on endpoint failure in tests/integration/test_message_sender.py
- [ ] T045 [US2] End-to-end test for error generation → transmission workflow in tests/integration/test_generation_to_output.py

### Implementation for User Story 2

- [ ] T046 [P] [US2] Implement MessageSenderService with endpoint configuration in src/services/message_sender.py
- [ ] T047 [US2] Add message formatting for external consumption (JSON serialization) in src/services/message_sender.py
- [ ] T048 [US2] Implement transmission logic with HTTP client in src/services/message_sender.py
- [ ] T049 [US2] Add error handling and message queueing for endpoint unavailability in src/services/message_sender.py
- [ ] T050 [US2] Add chronological ordering for message transmission in src/services/message_sender.py
- [ ] T051 [US2] Add observability (trace IDs, transmission status, delivery confirmation) to MessageSenderService
- [ ] T052 [P] [US2] Create workshop notebook demonstrating message output in notebooks/demos/02_message_output_demo.ipynb
- [ ] T053 [US2] Integrate ErrorGeneratorAgent with MessageSenderService in src/agents/error_generator.py

**Checkpoint**: User Stories 1 AND 2 both work - can generate and transmit errors independently

---

## Phase 5: User Story 3 - Remediation Command Reception (Priority: P3)

**Goal**: Receive JSON remediation commands from external source, validate against schema, and queue for processing

**Independent Test**: Send various JSON commands (config_change, os_reconfig, restart) with valid and invalid payloads. Verify parsing, validation, and queueing. Test command ordering for same resource

### Tests for User Story 3

- [ ] T054 [P] [US3] Contract test for RemediationCommand JSON schema in tests/contract/test_remediation_command_schema.py
- [ ] T055 [P] [US3] Unit test for command validation (all action types) in tests/unit/test_command_validation.py
- [ ] T056 [P] [US3] Unit test for command queueing and ordering in tests/unit/test_command_receiver.py
- [ ] T057 [P] [US3] Mock LLM test for orchestrator agent with command routing in tests/integration/test_orchestrator_agent.py
- [ ] T058 [US3] Integration test for command reception → orchestration workflow in tests/integration/test_command_reception_workflow.py

### Implementation for User Story 3

- [ ] T059 [P] [US3] Implement CommandReceiverService with JSON parsing in src/services/command_receiver.py
- [ ] T060 [US3] Add schema validation using RemediationCommand model in src/services/command_receiver.py
- [ ] T061 [US3] Implement command queue with priority ordering in src/services/command_receiver.py
- [ ] T062 [US3] Add conflict detection for commands targeting same resource in src/services/command_receiver.py
- [ ] T063 [P] [US3] Design prompt templates for orchestration (agent selection) in src/prompts/orchestration.py
- [ ] T064 [US3] Implement OrchestratorAgent for command routing in src/agents/orchestrator.py
- [ ] T065 [US3] Add LLM integration for intelligent agent selection in src/agents/orchestrator.py
- [ ] T066 [US3] Add risk assessment and validation requirements in src/agents/orchestrator.py
- [ ] T067 [US3] Add observability (trace IDs, routing decisions, rationale logging) to OrchestratorAgent
- [ ] T068 [P] [US3] Create workshop notebook demonstrating command reception in notebooks/demos/03_command_reception_demo.ipynb

**Checkpoint**: User Stories 1-3 complete - full data flow from generation → output → reception → orchestration

---

## Phase 6: User Story 4 - IRIS Configuration Agent (Priority: P4)

**Goal**: Execute IRIS configuration changes by modifying CPF files, determine restart requirements, and provide rollback on failure

**Independent Test**: Provide config_change commands for various CPF settings (Startup/globals, config section). Verify CPF modifications, restart requirement determination, backup creation, and rollback on failure

### Tests for User Story 4

- [ ] T069 [P] [US4] Unit test for CPF file modification in tests/unit/test_cpf_manager.py
- [ ] T070 [P] [US4] Unit test for restart requirement determination in tests/unit/test_config_agent.py
- [ ] T071 [P] [US4] Unit test for CPF backup and rollback in tests/unit/test_cpf_manager.py
- [ ] T072 [P] [US4] Mock LLM test for config agent with mocked file system in tests/integration/test_config_agent.py
- [ ] T073 [US4] Integration test for end-to-end config change workflow in tests/integration/test_config_workflow.py

### Implementation for User Story 4

- [ ] T074 [P] [US4] Extend CPF manager with backup/rollback capabilities in src/services/cpf_manager.py
- [ ] T075 [US4] Add restart requirement determination (LLM-assisted for ambiguous cases) in src/services/cpf_manager.py
- [ ] T076 [P] [US4] Design prompt templates for config validation in src/prompts/validation.py
- [ ] T077 [US4] Implement ConfigAgent with CPF modification logic in src/agents/config_agent.py
- [ ] T078 [US4] Add pre-condition validation (file permissions, CPF existence) in src/agents/config_agent.py
- [ ] T079 [US4] Add post-modification validation (CPF syntax check) in src/agents/config_agent.py
- [ ] T080 [US4] Implement ConfigAgentResponse structured output in src/agents/config_agent.py
- [ ] T081 [US4] Add observability (trace IDs, before/after values, restart determination) to ConfigAgent
- [ ] T082 [P] [US4] Create workshop notebook demonstrating config changes in notebooks/demos/04_config_agent_demo.ipynb

**Checkpoint**: User Story 4 complete - can execute IRIS configuration changes independently

---

## Phase 7: User Story 5 - OS Reconfiguration Agent (Priority: P5)

**Goal**: Execute OS-level changes (memory allocation, CPU configuration) with validation and rollback

**Independent Test**: Provide os_reconfig commands for memory (huge pages) and CPU settings. Verify appropriate system commands are executed, resources are validated, and rollback occurs on failure

### Tests for User Story 5

- [ ] T083 [P] [US5] Unit test for huge pages calculation and validation in tests/unit/test_os_agent.py
- [ ] T084 [P] [US5] Unit test for subprocess command construction in tests/unit/test_os_agent.py
- [ ] T085 [P] [US5] Unit test for permission validation in tests/unit/test_os_agent.py
- [ ] T086 [P] [US5] Mock subprocess test for OS agent with mocked commands in tests/integration/test_os_agent.py
- [ ] T087 [US5] Integration test for OS reconfiguration workflow in tests/integration/test_os_workflow.py

### Implementation for User Story 5

- [ ] T088 [P] [US5] Implement OS resource validation (/proc/meminfo parsing) in src/agents/os_agent.py
- [ ] T089 [US5] Implement memory allocation logic (huge pages, shared memory) in src/agents/os_agent.py
- [ ] T090 [US5] Implement CPU configuration logic (affinity, allocation) in src/agents/os_agent.py
- [ ] T091 [US5] Add subprocess execution with timeout and error capture in src/agents/os_agent.py
- [ ] T092 [US5] Add permission validation before OS changes in src/agents/os_agent.py
- [ ] T093 [US5] Add post-change validation (verify settings in effect) in src/agents/os_agent.py
- [ ] T094 [US5] Implement OSAgentResponse structured output in src/agents/os_agent.py
- [ ] T095 [US5] Add observability (trace IDs, commands executed, validation results) to OSAgent
- [ ] T096 [P] [US5] Create workshop notebook demonstrating OS changes in notebooks/demos/05_os_agent_demo.ipynb

**Checkpoint**: User Story 5 complete - can execute OS-level changes independently

---

## Phase 8: User Story 6 - Instance Restart Agent (Priority: P6)

**Goal**: Manage IRIS instance restart operations (graceful with connection draining, forced for emergency) with startup verification

**Independent Test**: Trigger graceful and forced restart scenarios. Verify connection draining, shutdown sequences, startup monitoring, and operational validation. Test timeout handling

### Tests for User Story 6

- [ ] T097 [P] [US6] Unit test for connection tracking and draining in tests/unit/test_restart_agent.py
- [ ] T098 [P] [US6] Unit test for shutdown command construction in tests/unit/test_restart_agent.py
- [ ] T099 [P] [US6] Unit test for startup log monitoring in tests/unit/test_restart_agent.py
- [ ] T100 [P] [US6] Mock subprocess test for restart agent with mocked IRIS commands in tests/integration/test_restart_agent.py
- [ ] T101 [US6] Integration test for graceful and forced restart workflows in tests/integration/test_restart_workflow.py

### Implementation for User Story 6

- [ ] T102 [P] [US6] Implement connection tracking and draining logic in src/agents/restart_agent.py
- [ ] T103 [US6] Implement graceful shutdown sequence with timeout in src/agents/restart_agent.py
- [ ] T104 [US6] Implement forced shutdown for emergency scenarios in src/agents/restart_agent.py
- [ ] T105 [US6] Implement IRIS startup monitoring (log parsing for initialization) in src/agents/restart_agent.py
- [ ] T106 [US6] Add post-startup validation (connection test, database mount check) in src/agents/restart_agent.py
- [ ] T107 [US6] Implement RestartAgentResponse structured output in src/agents/restart_agent.py
- [ ] T108 [US6] Add observability (trace IDs, connection counts, shutdown/startup status) to RestartAgent
- [ ] T109 [P] [US6] Create workshop notebook demonstrating restart operations in notebooks/demos/06_restart_agent_demo.ipynb

**Checkpoint**: All user stories complete - full system operational

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T110 [P] Create tutorial notebook for agent architecture introduction in notebooks/tutorials/01_introduction_to_agents.ipynb
- [ ] T111 [P] Create tutorial notebook for building custom agents in notebooks/tutorials/02_building_custom_agents.ipynb
- [ ] T112 [P] Create tutorial notebook for agent testing patterns in notebooks/tutorials/03_agent_testing_patterns.ipynb
- [ ] T113 [P] Create orchestration demo notebook showing full workflow in notebooks/demos/02_remediation_workflow_demo.ipynb
- [ ] T114 [P] Add comprehensive docstrings to all agent classes with examples
- [ ] T115 [P] Add inline comments explaining agent patterns in src/agents/
- [ ] T116 [P] Create architecture diagram for README.md showing agent interactions
- [ ] T117 [US3] Implement command execution status reporting (pending, in-progress, completed, failed) in src/services/command_receiver.py
- [ ] T118 Code review and refactoring for consistency across agents
- [ ] T119 Performance optimization for LLM calls (prompt minimization, caching)
- [ ] T120 Security hardening (input sanitization, API key protection in logs)
- [ ] T121 Run all acceptance scenarios from spec.md to validate completeness
- [ ] T122 Run quickstart.md validation to ensure all examples work
- [ ] T123 Update README.md with final usage instructions and architecture overview

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4 → P5 → P6)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories ✅ MVP
- **User Story 2 (P2)**: Can start after Foundational - Integrates with US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational - Independent (command reception and orchestration)
- **User Story 4 (P4)**: Can start after Foundational - Depends on US3 for orchestrator routing
- **User Story 5 (P5)**: Can start after Foundational - Depends on US3 for orchestrator routing
- **User Story 6 (P6)**: Can start after Foundational - Depends on US3 for orchestrator routing

**Note**: US4, US5, US6 can be developed in parallel once US3 (orchestration) is complete since each agent operates on different resources.

### Within Each User Story

1. Tests FIRST (write, ensure they FAIL)
2. Models (if needed for that story)
3. Services (if needed for that story)
4. Agent implementation
5. Observability and cost tracking
6. Workshop notebooks
7. Story complete - validate independently

### Parallel Opportunities

**Phase 1 (Setup)**: T002-T007 can all run in parallel (different files)

**Phase 2 (Foundational)**: 
- Infrastructure: T008-T014 can run in parallel
- Models: T015-T018 can run in parallel
- Services: T019-T020 can run in parallel
- Tests: T021-T027 can run in parallel

**User Story 1**: T028-T032 (tests) in parallel, then T033-T034 (models/prompts) in parallel

**User Story 2**: T042-T044 (tests) in parallel, then T046 (service creation) in parallel

**User Story 3**: T054-T057 (tests) in parallel, then T059, T063 (service and prompts) in parallel

**User Story 4**: T069-T072 (tests) in parallel, then T074, T076 (service and prompts) in parallel

**User Story 5**: T083-T086 (tests) in parallel

**User Story 6**: T097-T100 (tests) in parallel

**Polish Phase**: T110-T116, T120-T122 can all run in parallel (different files)

**Multi-Story Parallel**: Once Phase 2 completes, US1, US2, US3 can all start in parallel. Once US3 completes, US4, US5, US6 can all proceed in parallel.

---

## Parallel Example: User Story 1

```bash
# Write all tests for US1 in parallel:
T028: "Unit test for error pattern extraction in tests/unit/test_error_pattern_extraction.py"
T029: "Unit test for ErrorGenerationRequest model in tests/unit/test_error_generation_request.py"
T030: "Mock LLM test for error generation in tests/integration/test_error_generator_agent.py"
T031: "Prompt regression test in tests/prompts/test_error_prompts.py"

# Then create models and prompts in parallel:
T033: "Create ErrorGenerationRequest model in src/models/error_message.py"
T034: "Design prompt templates in src/prompts/error_generation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Recommended approach for workshop development:**

1. ✅ Complete Phase 1: Setup (~30 minutes)
2. ✅ Complete Phase 2: Foundational (~2-3 hours) - CRITICAL checkpoint
3. ✅ Complete Phase 3: User Story 1 (~3-4 hours with tests)
4. **STOP and VALIDATE**: Test error generation independently, create demo notebook
5. Deploy/demo - you now have a working error simulator!

**Estimated time to MVP**: ~6-8 hours

### Incremental Delivery

**Build value progressively:**

1. **Foundation** (Phases 1-2): Core infrastructure ready → ~3-4 hours
2. **+US1** (Phase 3): Error generation → Test independently → Demo (MVP!) → ~3-4 hours
3. **+US2** (Phase 4): External output → Test independently → Demo → ~2-3 hours
4. **+US3** (Phase 5): Command reception → Test independently → Demo → ~3-4 hours
5. **+US4** (Phase 6): Config agent → Test independently → Demo → ~3-4 hours
6. **+US5** (Phase 7): OS agent → Test independently → Demo → ~2-3 hours
7. **+US6** (Phase 8): Restart agent → Test independently → Demo → ~2-3 hours
8. **Polish** (Phase 9): Tutorials, docs, refinement → ~2-3 hours

**Total estimated time**: ~20-27 hours for full system

### Parallel Team Strategy

**With 3 developers after Foundational phase completion:**

- **Developer A**: User Story 1 → User Story 4 (error gen → config agent)
- **Developer B**: User Story 2 → User Story 5 (message output → OS agent)
- **Developer C**: User Story 3 → User Story 6 (command reception → restart agent)

**Timeline with parallel development**: ~12-15 hours wall-clock time

---

## Task Summary

- **Total Tasks**: 123
- **Setup Tasks**: 7 (T001-T007)
- **Foundational Tasks**: 19 (T008-T027)
- **User Story 1 Tasks**: 14 (T028-T041) - Including 5 tests
- **User Story 2 Tasks**: 12 (T042-T053) - Including 4 tests
- **User Story 3 Tasks**: 15 (T054-T068) - Including 5 tests
- **User Story 4 Tasks**: 14 (T069-T082) - Including 5 tests
- **User Story 5 Tasks**: 14 (T083-T096) - Including 5 tests
- **User Story 6 Tasks**: 13 (T097-T109) - Including 5 tests
- **Polish Tasks**: 14 (T110-T123)

**Test Tasks**: 34 total (constitution-mandated Test-Driven AI)  
**Parallel Opportunities**: ~45 tasks marked [P] can run in parallel  
**MVP Scope**: Phases 1-3 (T001-T041) = 40 tasks for working error simulator

---

## Validation & Quality Gates

### After Phase 2 (Foundational)
- ✅ All unit tests for foundational models pass
- ✅ Logging captures trace IDs correctly
- ✅ Cost tracker counts tokens accurately
- ✅ LLM client can complete structured output requests

### After Phase 3 (US1 - MVP)
- ✅ All US1 tests pass (5 tests)
- ✅ Can generate errors for all 4 categories (config, license, OS, journal)
- ✅ Error format matches IRIS message.log format
- ✅ Demo notebook runs successfully
- ✅ Token usage under budget (500 tokens per generation)

### After Each Subsequent User Story
- ✅ All story-specific tests pass
- ✅ Story works independently without other stories
- ✅ Demo notebook demonstrates story functionality
- ✅ Observability logging captures all operations
- ✅ Cost tracking shows token usage within budget

### Final Validation (Before Phase 9 Completion)
- ✅ All 34 test files pass
- ✅ All 30+ acceptance scenarios from spec.md validated
- ✅ All quickstart.md examples execute successfully
- ✅ Constitution check: All 7 principles satisfied
- ✅ Total token budget under 500K tokens/day for 20 users

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] labels**: Map each task to specific user story for traceability
- **Tests first**: Constitution mandates Test-Driven AI - write failing tests before implementation
- **Independent stories**: Each user story should be completable and testable without others
- **String-based communication**: All agent inputs/outputs use JSON strings (spec requirement)
- **MVP mindset**: Stop at Phase 3 to validate core capability before expanding
- **Workshop focus**: Extensive notebooks and tutorials support educational goals
- **Observability**: Every agent operation logged with trace IDs for debugging
- **Cost consciousness**: Token tracking and budget alerts prevent runaway costs
