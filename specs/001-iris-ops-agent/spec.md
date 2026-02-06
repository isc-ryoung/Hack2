# Feature Specification: Instance - IRIS Operations Agent

**Feature Branch**: `001-iris-ops-agent`  
**Created**: 2026-02-06  
**Status**: Draft  
**Input**: User description: "An Agentic AI project, called Instance, that emulates an InterSystems IRIS database platform system. This project should create one or more AI Agents and associated orchestration. It should provide generated simulated error messages as if they were from the messages.log file. There is a sample messages.log in the folder log_samples. The sort of errors that might be generated could be related to configuration settings that need to be modified which may or may not require an IRIS instance restart or a license issue or errors related to changes required to the operating system such as CPU or memory. The generated messages would be sent to an external consumer which is not part of this project. This project would also consume external messages from a system which are in a JSON format and provide commands for how to rectify the errors. Depending on the error this project would call one or more Agentic AI tools to perform the command. The tools could be to make IRIS system configuration changes, to reconfigure the operating system or to restart the IRIS instance."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Error Message Generation (Priority: P1)

The system generates realistic IRIS error messages based on patterns observed in actual messages.log files. These simulated errors should cover common operational issues including configuration problems, license issues, and resource constraints. The generated messages follow the same format as real IRIS logs.

**Why this priority**: Error generation is the foundation of the simulation system. Without realistic error messages, the downstream remediation agents cannot be tested or demonstrated. This provides immediate value for training and testing scenarios.

**Independent Test**: Can be fully tested by triggering error generation and verifying the output matches IRIS message.log format with appropriate error types (config, license, OS resource issues). Delivers standalone value for IRIS error simulation and testing.

**Acceptance Scenarios**:

1. **Given** the system is initialized, **When** a configuration error simulation is requested, **Then** a message is generated with appropriate CPF file parsing error format including timestamp, process ID, and severity level
2. **Given** the system is initialized, **When** a license error simulation is requested, **Then** a message is generated matching LMF error patterns (e.g., "No valid license key" or license expiration warnings)
3. **Given** the system is initialized, **When** a resource constraint error is requested, **Then** a message is generated indicating memory allocation issues or CPU constraints in IRIS message format
4. **Given** the system is initialized, **When** a journal error simulation is requested, **Then** a message is generated with journal directory permission or locking errors
5. **Given** error messages are generated, **When** messages are formatted for output, **Then** they include timestamp, process ID, severity level, category tags, and descriptive error text matching observed patterns in log_samples/messages.log

---

### User Story 2 - External Message Output (Priority: P2)

The system sends generated error messages to an external consumer system. Messages are formatted and transmitted through a defined interface, allowing external monitoring and alerting systems to receive IRIS operational events.

**Why this priority**: While error generation is foundational, the value multiplies when those errors can be consumed by external systems for monitoring, alerting, and analysis. This enables integration with broader operational workflows.

**Independent Test**: Can be fully tested by generating errors and verifying they are transmitted to a configured external endpoint. Message delivery confirmation provides validation. Delivers value for integration scenarios without requiring remediation agents.

**Acceptance Scenarios**:

1. **Given** error messages are generated, **When** the output interface is configured, **Then** messages are formatted for external consumption (JSON or structured format)
2. **Given** messages are formatted, **When** the external consumer endpoint is available, **Then** messages are successfully transmitted
3. **Given** message transmission is attempted, **When** the external consumer is unavailable, **Then** messages are queued or logged with appropriate error handling
4. **Given** multiple error messages exist, **When** transmission occurs, **Then** messages are sent in chronological order maintaining operational context

---

### User Story 3 - Remediation Command Reception (Priority: P3)

The system receives JSON-formatted remediation commands from an external source. These commands specify actions to resolve identified IRIS operational issues, including required parameters and execution context.

**Why this priority**: Command reception enables the system to respond to operational issues. This bridges monitoring (error generation) with action (remediation), though it doesn't execute actions yet. Essential for closed-loop operational automation.

**Independent Test**: Can be fully tested by sending various JSON command messages and verifying they are correctly parsed, validated, and queued for processing. Delivers value for command protocol validation independent of execution agents.

**Acceptance Scenarios**:

1. **Given** an external system sends a JSON remediation command, **When** the command is received, **Then** it is parsed and validated against the expected schema
2. **Given** a command specifies configuration changes, **When** validation occurs, **Then** required parameters (config file, setting name, value) are confirmed present
3. **Given** a command specifies instance restart, **When** validation occurs, **Then** restart parameters (graceful vs forced, timeout) are validated
4. **Given** a command specifies OS reconfiguration, **When** validation occurs, **Then** OS-level parameters (memory, CPU settings) are validated
5. **Given** an invalid command is received, **When** validation fails, **Then** appropriate error response is generated with details of validation failure
6. **Given** valid commands are received, **When** multiple commands target the same resource, **Then** commands are ordered appropriately to avoid conflicts

---

### User Story 4 - IRIS Configuration Agent (Priority: P4)

An agent executes IRIS system configuration changes based on received commands. The agent understands IRIS CPF file structure, configuration parameters, and determines whether changes require instance restart.

**Why this priority**: Configuration changes are the most common remediation action for IRIS systems. This agent delivers tangible operational value by automating routine configuration tasks and reducing manual intervention.

**Independent Test**: Can be fully tested by providing configuration change commands and verifying CPF file modifications, validation of settings, and correct restart requirement determination. Delivers value for configuration automation independent of other agents.

**Acceptance Scenarios**:

1. **Given** a configuration change command is received, **When** the config agent processes it, **Then** the appropriate CPF file section is identified
2. **Given** CPF file section is identified, **When** the setting is modified, **Then** changes are applied correctly and validated
3. **Given** a configuration change is made, **When** restart requirement is evaluated, **Then** the agent correctly determines if IRIS instance restart is required based on configuration parameter type
4. **Given** changes require restart, **When** the agent completes configuration update, **Then** a restart recommendation is provided with justification
5. **Given** configuration change fails, **When** errors occur, **Then** changes are rolled back and error details are logged
6. **Given** multiple configuration changes are requested, **When** changes are applied, **Then** they are batched appropriately to minimize restart cycles

---

### User Story 5 - OS Reconfiguration Agent (Priority: P5)

An agent executes operating system level changes including memory allocation and CPU configuration adjustments. The agent understands OS-specific commands and validates changes are appropriate for IRIS workload requirements.

**Why this priority**: OS-level issues require different tooling and permissions than IRIS configuration. This agent handles infrastructure-level remediation, completing the operational automation stack.

**Independent Test**: Can be fully tested by providing OS reconfiguration commands and verifying appropriate system commands are executed, resources are adjusted, and changes are validated. Delivers value for infrastructure automation.

**Acceptance Scenarios**:

1. **Given** a memory allocation command is received, **When** the OS agent processes it, **Then** available memory is verified before attempting changes
2. **Given** memory changes are validated, **When** allocation is modified, **Then** appropriate OS commands are executed (e.g., huge pages configuration, shared memory limits)
3. **Given** CPU configuration command is received, **When** the OS agent processes it, **Then** CPU affinity or allocation commands are generated correctly
4. **Given** OS changes are attempted, **When** insufficient permissions exist, **Then** appropriate error messages are generated with required permission details
5. **Given** OS changes are completed, **When** validation occurs, **Then** the agent confirms changes are in effect and IRIS can utilize new resources
6. **Given** OS changes fail, **When** rollback is needed, **Then** previous configuration is restored where possible

---

### User Story 6 - Instance Restart Agent (Priority: P6)

An agent manages IRIS instance restart operations including graceful shutdown with connection draining, forced shutdown for emergency scenarios, and startup verification.

**Why this priority**: Restart operations are the final step in many remediation workflows. This agent ensures clean restarts, minimizing downtime and preventing data corruption during operational maintenance.

**Independent Test**: Can be fully tested by triggering restart scenarios (graceful, forced) and verifying proper shutdown sequences, startup completion, and operational validation. Delivers value for restart automation and reliability.

**Acceptance Scenarios**:

1. **Given** a graceful restart command is received, **When** the restart agent processes it, **Then** active connections are identified and given time to drain
2. **Given** connection draining is complete, **When** shutdown proceeds, **Then** IRIS shutdown sequence is initiated with appropriate flags
3. **Given** shutdown is initiated, **When** timeout is reached, **Then** the agent determines whether to proceed with forced shutdown
4. **Given** forced restart command is received, **When** immediate shutdown is needed, **Then** IRIS is stopped without connection draining
5. **Given** IRIS is stopped, **When** startup is initiated, **Then** the agent monitors startup log for successful initialization
6. **Given** startup completes, **When** validation occurs, **Then** the agent confirms IRIS is accepting connections and databases are mounted correctly
7. **Given** restart fails, **When** errors occur during shutdown or startup, **Then** detailed error information is captured and appropriate recovery actions are suggested

---

### Edge Cases

- What happens when multiple remediation commands conflict (e.g., config change requiring restart vs immediate restart command)?
- How does the system handle partial failures (e.g., config change succeeds but restart fails)?
- What happens when external message consumer is unreachable for extended periods?
- How does the system handle cascading errors (e.g., OS memory change triggers IRIS config change triggers restart)?
- What happens when agent permissions are insufficient for requested operations?
- How does the system behave when receiving malformed JSON commands?
- What happens when IRIS instance is already in a failed state when remediation is attempted?
- How does the system handle very high volumes of error generation requests?
- What happens when log_samples/messages.log patterns don't match specific error types requested?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate simulated IRIS error messages following the format observed in messages.log (timestamp, process ID, severity level, category tag, message text)
- **FR-002**: System MUST support error generation for at least four categories: configuration errors, license errors, OS resource errors, and journal errors
- **FR-003**: System MUST parse and learn from the sample messages.log file in log_samples directory to generate realistic error patterns
- **FR-004**: System MUST transmit generated error messages to external consumer system through configurable interface
- **FR-005**: System MUST receive JSON-formatted remediation commands from external source
- **FR-006**: System MUST validate received JSON commands against defined schema before processing
- **FR-007**: System MUST implement IRIS configuration agent capable of modifying CPF file settings
- **FR-008**: System MUST determine whether configuration changes require IRIS instance restart
- **FR-009**: System MUST implement OS reconfiguration agent capable of adjusting memory and CPU settings
- **FR-010**: System MUST implement instance restart agent supporting both graceful and forced restart modes
- **FR-011**: System MUST provide structured logging of all agent actions with trace IDs for troubleshooting
- **FR-012**: System MUST handle agent failures gracefully with rollback capabilities where applicable
- **FR-013**: System MUST queue remediation commands when multiple commands are received simultaneously
- **FR-014**: System MUST provide command execution status reporting (pending, in-progress, completed, failed)
- **FR-015**: Agents MUST validate pre-conditions before executing remediation actions (e.g., check file permissions, verify IRIS is running)
- **FR-016**: System MUST support configurable agent orchestration for complex remediation workflows
- **FR-017**: System MUST integrate with LLM for intelligent error message generation based on patterns
- **FR-018**: System MUST integrate with LLM for command interpretation and execution planning

### Key Entities *(include if feature involves data)*

- **Error Message**: Simulated IRIS operational message containing timestamp, process ID, severity level (0-3), category tag (e.g., Generic.Event, Database, Utility.Event, WriteDaemon), and descriptive text. Generated based on patterns from sample logs.

- **Remediation Command**: JSON-structured instruction received from external system specifying action type (config_change, os_reconfig, restart), target parameters, and execution context. Validated and queued for agent processing.

- **Agent**: Specialized component responsible for specific remediation actions (ConfigAgent, OSAgent, RestartAgent). Each agent has execution logic, pre-condition validation, and rollback capabilities.

- **Execution Context**: Runtime state including current IRIS instance status, OS resource availability, pending commands queue, and active agent operations. Tracks dependencies and conflicts between commands.

- **Audit Log**: Structured record of all agent actions including command received, agent invoked, execution result, and any errors encountered. Includes trace IDs for correlation across distributed operations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System generates error messages that match IRIS messages.log format with 95%+ accuracy when validated against sample logs
- **SC-002**: Generated error messages are successfully transmitted to external consumer within 1 second of generation
- **SC-003**: JSON remediation commands are parsed and validated within 100ms of receipt
- **SC-004**: Configuration agent successfully modifies CPF settings with 100% accuracy for supported parameters
- **SC-005**: Instance restart agent completes graceful shutdown within configurable timeout (default 60 seconds) for 90% of cases
- **SC-006**: System handles remediation command failures with automatic rollback preventing inconsistent states

### AI-Specific Success Criteria *(if applicable)*

- **AI-001**: LLM-generated error messages are contextually appropriate for the specified error category (config, license, OS, journal) in 90%+ of cases based on human evaluation
- **AI-002**: Agent orchestration using LLM determines correct agent selection for remediation commands with 95%+ accuracy
- **AI-003**: Average LLM token usage per error generation is under 500 tokens to maintain cost effectiveness
- **AI-004**: Agent execution planning by LLM identifies correct pre-conditions and dependencies in 95%+ of multi-step remediation workflows
- **AI-005**: End-to-end remediation workflow (receive command → execute agents → validate result) completes within 10 seconds for 90% of single-agent operations

## Assumptions *(optional - document assumptions made)*

1. **IRIS Installation**: System assumes IRIS instance is installed and accessible on the target system where agents will execute
2. **File System Access**: Agents assume read/write access to IRIS configuration directory (/usr/local/IRIS/ or equivalent) and OS configuration files
3. **Network Connectivity**: External message consumer and command source maintain reliable network connectivity with acceptable latency (<1s)
4. **JSON Schema**: Remediation commands follow a predefined JSON schema that will be documented in the implementation plan
5. **OS Support**: Initial implementation targets Linux environments (Red Hat Enterprise Linux) as evident from sample logs
6. **Authentication**: External message interfaces assume pre-established authentication mechanisms (API keys, certificates) are configured
7. **LLM Availability**: System assumes OpenAI API or equivalent LLM service is accessible for intelligent generation and orchestration
8. **Sample Log Representativeness**: The log_samples/messages.log file contains representative patterns for all error types to be simulated
9. **Single Instance**: Initial scope targets single IRIS instance management; cluster/mirror configurations are future enhancements
10. **Graceful Degradation**: When LLM is unavailable, agents fall back to rule-based processing for known command patterns

## Out of Scope *(optional - explicitly state what is NOT included)*

1. **External Consumer Implementation**: The actual external monitoring/alerting system that receives generated messages is not part of this project
2. **External Command Source**: The system that sends JSON remediation commands is not part of this project
3. **IRIS Installation/Licensing**: System does not install IRIS or manage licensing beyond detecting and simulating license errors
4. **Multi-Instance Management**: Sharded mirror configurations, and distributed IRIS deployments are not included
5. **Real-time Monitoring**: System simulates errors but does not monitor actual IRIS instance for real errors
6. **User Interface**: No web UI or dashboard for configuration or monitoring; system operates via APIs and configuration files
7. **Historical Error Analysis**: System does not analyze past IRIS logs for patterns beyond the provided sample log
8. **Custom Error Types**: Only predefined error categories (config, license, OS, journal) are supported; arbitrary error simulation is not included
9. **Production Safety Guarantees**: This is a simulation/workshop project; production-grade safety mechanisms (backups before changes, extensive testing) are simplified
10. **Cross-Platform Support**: Initial version targets Linux only; Windows and cloud-specific configurations are future work

## Notes *(optional - additional context)*

### Technical Context

This project serves as both a practical operational automation tool and an educational platform for agentic AI patterns. The design emphasizes:

- **Clear Agent Boundaries**: Each agent (Config, OS, Restart) has single responsibility for maintainability
- **Observable AI Operations**: All LLM calls, agent decisions, and execution steps are logged with trace IDs
- **Educational Value**: Code includes extensive documentation and notebook examples demonstrating agent patterns
- **Realistic Simulation**: Error generation based on actual IRIS logs ensures practical relevance

### IRIS Domain Knowledge

InterSystems IRIS is an enterprise data platform with specific operational characteristics:
- **CPF Files**: Configuration Parameter Files control IRIS behavior; changes to some parameters require restart while others are dynamic
- **Journal System**: IRIS uses Write-Image Journaling (WIJ) for transaction durability; journal errors can freeze the system
- **Shared Memory**: IRIS uses large shared memory segments for global buffers; OS configuration affects IRIS performance
- **Startup Sequence**: IRIS has complex initialization including database mounting, namespace setup, and service activation

### Agent Orchestration Patterns

The project demonstrates key agentic AI patterns:
- **Error Analysis Agent**: Uses LLM to classify error types and determine severity from log patterns
- **Remediation Planning Agent**: Uses LLM to interpret commands and select appropriate execution agents
- **Validation Agent**: Uses LLM to verify pre-conditions and post-conditions for safe execution
- **Coordination**: Multiple agents may need to work together (e.g., config change → validation → restart)

### Real-world Applicability

While designed for workshops, patterns demonstrated here apply to real operational scenarios:
- Automated incident response for database platforms
- Intelligent alert correlation and remediation
- Safe automation of routine maintenance tasks
- Integration of human approval workflows for high-risk operations
