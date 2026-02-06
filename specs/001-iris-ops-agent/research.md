# Research: Instance - IRIS Operations Agent

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Created**: 2026-02-06  
**Purpose**: Document technology decisions, patterns, and best practices for implementation

## Phase 0: Technology Research & Decisions

### 1. OpenAI Agents SDK Pattern

**Decision**: Use OpenAI Agents SDK (openai-agents-python) with structured outputs via Pydantic models

**Rationale**:
- Native support for structured outputs using `response_format` with Pydantic models
- Built-in agent orchestration patterns (handoffs, tool calling)
- Simplified LLM interaction handling (retries, streaming, error recovery)
- Strong typing with Pydantic integration ensures data validation
- Educational value - demonstrates modern agent patterns

**Implementation Pattern**:
```python
from openai import OpenAI
from pydantic import BaseModel

class ErrorMessage(BaseModel):
    timestamp: str
    process_id: int
    severity: int
    category: str
    message_text: str

client = OpenAI()
response = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[{"role": "user", "content": prompt}],
    response_format=ErrorMessage
)
structured_output = response.choices[0].message.parsed
```

**Alternatives Considered**:
- **LangChain**: More complex abstraction, unnecessary for single-process agents
- **Autogen**: Overkill for this use case, focused on multi-agent conversations
- **Direct OpenAI API**: Rejected - reinventing structured output parsing

**Best Practices**:
- Define all agent outputs as Pydantic models for type safety
- Use `gpt-4o-2024-08-06` for structured outputs (native support)
- Implement fallback to `gpt-3.5-turbo` for cost-effective simple operations
- Cache structured output schemas to reduce parsing overhead

---

### 2. Agent Communication Architecture

**Decision**: String-based synchronous communication within single Python process

**Rationale**:
- Specification requirement: "communication to and from external systems should include calls with strings as they may be within the same Python process"
- Simplifies workshop/educational scenarios - no networking complexity
- Enables synchronous debugging and tracing
- Pydantic models serialize to/from JSON strings naturally
- Aligns with constitution's educational clarity principle

**Implementation Pattern**:
```python
# Agent outputs are Pydantic models that serialize to JSON strings
orchestrator_response_str = orchestrator_agent.execute(command_json_str)
orchestrator_response = OrchestratorResponse.model_validate_json(orchestrator_response_str)

# Route to appropriate agent based on orchestrator decision
if orchestrator_response.agent_type == "config":
    result_str = config_agent.execute(orchestrator_response.command_str)
    result = ConfigAgentResponse.model_validate_json(result_str)
```

**Alternatives Considered**:
- **Message Queues (RabbitMQ, Redis)**: Rejected - over-engineering for workshop, adds deployment complexity
- **gRPC/HTTP APIs**: Rejected - unnecessary network overhead, harder to debug
- **Direct object passing**: Rejected - doesn't match spec requirement for string-based communication

**Best Practices**:
- Always validate JSON strings with Pydantic on receipt (fail-fast validation)
- Include trace_id in all messages for correlation
- Log all inter-agent string exchanges for debugging
- Use `model_dump_json()` for serialization, `model_validate_json()` for deserialization

---

### 3. IRIS Log Pattern Extraction

**Decision**: LLM-powered pattern extraction from log_samples/messages.log with fallback to regex templates

**Rationale**:
- Sample log contains 49,450 lines with rich error patterns
- LLM can extract nuanced patterns (timestamp formats, severity levels, category structures)
- Fallback ensures system works even if LLM unavailable
- Educational value - demonstrates LLM use for pattern learning

**Implementation Approach**:
1. **Startup**: Parse log_samples/messages.log, extract 50-100 error examples by category
2. **Pattern Storage**: Store extracted patterns as JSON in `src/prompts/error_patterns.json`
3. **Generation**: Use patterns as few-shot examples in error generation prompts
4. **Fallback**: If LLM fails, use regex templates for known error types

**Pattern Categories** (from log analysis):
- **Configuration Errors**: CPF parsing errors, invalid settings (lines 855, 949)
- **License Errors**: "LMF Error: No valid license key" (line 133)
- **OS Resource Errors**: Memory allocation warnings, global buffer settings (line 76)
- **Journal Errors**: WIJ locking failures, permission denied (lines 1060-1068)
- **Database Errors**: Extent index rebuild errors, directory errors (lines 1188-1198)

**Best Practices**:
- Extract patterns during initialization, cache in memory
- Include severity distribution (0=info, 1=warning, 2=error, 3=fatal)
- Preserve timestamp format: `MM/DD/YY-HH:MM:SS:mmm`
- Maintain category tag format: `[Category.Subcategory]`

---

### 4. CPF File Management

**Decision**: Direct file I/O with INI-style parsing, LLM-assisted validation for complex settings

**Rationale**:
- IRIS CPF files use INI-like format with `[Section]` and `key=value` structure
- Python's `configparser` handles basic parsing
- LLM can determine restart requirements for ambiguous settings
- Rollback via file snapshots before modification

**Implementation Pattern**:
```python
import configparser
import shutil
from pathlib import Path

class CPFManager:
    def modify_setting(self, section: str, key: str, value: str) -> tuple[bool, bool]:
        """Returns (success, requires_restart)"""
        # 1. Backup current CPF
        backup_path = self.create_backup()
        
        try:
            # 2. Load and modify
            config = configparser.ConfigParser()
            config.read(self.cpf_path)
            config.set(section, key, value)
            
            # 3. Validate with LLM (does this require restart?)
            requires_restart = self.check_restart_requirement(section, key)
            
            # 4. Write changes
            with open(self.cpf_path, 'w') as f:
                config.write(f)
            
            return True, requires_restart
        except Exception as e:
            # Rollback on failure
            shutil.copy(backup_path, self.cpf_path)
            raise
```

**Settings Requiring Restart** (common cases):
- `[Startup]` section: All settings require restart
- `globals` (global buffers): Requires restart
- `routines` (routine buffers): Requires restart
- `[config]` section: Most require restart
- Dynamic settings: Journal switch, some database mounts

**Alternatives Considered**:
- **IRIS Management Portal API**: Rejected - requires running IRIS instance, adds complexity
- **ObjectScript via %SYS**: Rejected - requires IRIS runtime, harder to test

**Best Practices**:
- Always create backup before modification
- Validate CPF syntax after modification (try to parse it back)
- Use LLM to determine restart requirements for ambiguous cases
- Log all modifications with before/after values

---

### 5. OS Resource Management

**Decision**: Python subprocess calls to Linux commands with validation checks

**Rationale**:
- Target platform is Red Hat Enterprise Linux (from sample logs)
- Memory management: huge pages configuration, shared memory limits
- CPU management: core affinity, scheduler settings
- Subprocess allows controlled execution with timeout and error handling

**Implementation Pattern**:
```python
import subprocess
import shlex

class OSAgent:
    def configure_huge_pages(self, size_mb: int) -> bool:
        """Configure huge pages for IRIS shared memory"""
        # 1. Calculate number of pages needed
        page_count = size_mb // 2  # 2MB per huge page
        
        # 2. Validate available pages
        result = subprocess.run(
            ["cat", "/proc/meminfo"],
            capture_output=True, text=True, timeout=5
        )
        # Parse available huge pages from output
        
        # 3. Configure if available
        cmd = f"echo {page_count} > /proc/sys/vm/nr_hugepages"
        result = subprocess.run(
            shlex.split(cmd), capture_output=True, timeout=10
        )
        return result.returncode == 0
```

**OS Operations**:
- **Memory**: `sysctl vm.nr_hugepages`, `/proc/sys/vm/` settings
- **Shared Memory**: `/etc/sysctl.conf` modifications for `kernel.shmmax`, `kernel.shmall`
- **CPU Affinity**: `taskset` command for process pinning
- **Permissions**: Validate using `os.access()` before attempting changes

**Alternatives Considered**:
- **Ansible/Puppet**: Rejected - overkill for workshop, harder to integrate
- **Direct /proc writes**: Rejected - requires root, harder to validate

**Best Practices**:
- Always validate permissions before attempting OS changes
- Use `shlex.split()` to safely handle command arguments
- Set timeouts on all subprocess calls (5-10s)
- Capture stdout/stderr for error diagnosis
- Implement dry-run mode for validation without side effects

---

### 6. Structured Logging & Observability

**Decision**: Use `structlog` with JSON output, trace IDs via contextvars

**Rationale**:
- Constitution requirement: "All LLM calls, agent decisions, and execution steps are logged with trace IDs"
- JSON logs enable easy parsing and aggregation
- contextvars provide thread-safe trace ID propagation
- Rich context (agent name, operation, input/output, timing)

**Implementation Pattern**:
```python
import structlog
import contextvars
import uuid

trace_id_var = contextvars.ContextVar('trace_id', default=None)

def configure_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ]
    )

# Usage in agents
class ConfigAgent:
    def execute(self, command_str: str) -> str:
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)
        
        log = structlog.get_logger()
        log.info("config_agent_start", 
                 command=command_str, 
                 trace_id=trace_id)
        
        # ... execution ...
        
        log.info("config_agent_complete",
                 result=result_str,
                 trace_id=trace_id,
                 duration_ms=duration)
```

**Log Fields** (standard across all agents):
- `trace_id`: UUID for correlation
- `agent`: Agent name (error_generator, orchestrator, config, os, restart)
- `operation`: Operation being performed
- `input`: Sanitized input (no secrets)
- `output`: Sanitized output summary
- `duration_ms`: Operation duration
- `tokens_used`: LLM token count (if applicable)
- `cost_usd`: Estimated cost (if LLM used)
- `error`: Error details (if failed)

**Best Practices**:
- Sanitize API keys and sensitive data before logging
- Log before and after each agent operation
- Include token counts and costs for budget tracking
- Use consistent field names across all agents

---

### 7. Cost Management & Token Budgeting

**Decision**: Token tracking per operation with budget alerts, cached responses for repeated patterns

**Rationale**:
- Constitution requirement: Token tracking, budget alerts at 80%, optimization
- GPT-4o costs: ~$0.005/1K input tokens, ~$0.015/1K output tokens
- GPT-3.5-turbo costs: ~$0.0015/1K input tokens, ~$0.002/1K output tokens
- Budget: $0.50 per remediation workflow, 5K tokens per workflow

**Implementation Pattern**:
```python
class CostTracker:
    def __init__(self):
        self.session_tokens = 0
        self.session_cost = 0.0
        self.budget_limit = 0.50  # USD
        
    def track_llm_call(self, model: str, input_tokens: int, output_tokens: int):
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        self.session_tokens += (input_tokens + output_tokens)
        self.session_cost += cost
        
        if self.session_cost >= 0.80 * self.budget_limit:
            log.warning("budget_alert", 
                       used=self.session_cost,
                       limit=self.budget_limit,
                       percentage=80)
        
        return cost
```

**Cost Optimization Strategies**:
1. **Model Selection**: Use gpt-3.5-turbo for simple operations (command validation, pattern matching)
2. **Caching**: Cache error generation patterns, avoid regenerating same errors
3. **Prompt Optimization**: Minimize context, use concise system prompts
4. **Batch Processing**: Group multiple error generations in single LLM call
5. **Fallback**: Use rule-based processing when LLM budget exhausted

**Token Budget Allocation**:
- Error Generation: 500 tokens/error (400 input, 100 output)
- Command Orchestration: 800 tokens/command (600 input, 200 output)
- Validation: 400 tokens/validation (300 input, 100 output)
- Total per workflow: ~1700-5000 tokens depending on complexity

**Best Practices**:
- Track tokens at every LLM call
- Alert at 80% budget threshold
- Fail gracefully when budget exceeded (fallback to rule-based)
- Log all cost decisions for auditability

---

### 8. Testing Strategy

**Decision**: Pytest with mocked LLM responses (pytest-mock), fixture-based test data

**Rationale**:
- Constitution requirement: "Test-First Workflow"
- Unit tests for deterministic logic (parsing, validation)
- Integration tests with mocked LLM (predictable outputs)
- Prompt regression tests for critical prompts
- Real LLM tests in separate suite (CI with budget limits)

**Test Structure**:
```
tests/
├── unit/                       # Deterministic logic, no LLM
│   ├── test_log_parser.py
│   ├── test_cpf_manager.py
│   └── test_models.py
├── integration/                # With mocked LLM
│   ├── test_error_generator_agent.py
│   ├── test_orchestrator_agent.py
│   └── test_end_to_end_workflow.py
├── prompts/                    # Prompt regression
│   ├── test_error_prompts.py
│   └── test_orchestration_prompts.py
└── fixtures/
    ├── sample_messages.log
    ├── sample_iris.cpf
    └── mock_llm_responses.json
```

**Mock Pattern**:
```python
from pytest_mock import MockerFixture

def test_error_generator(mocker: MockerFixture):
    # Mock OpenAI API
    mock_response = ErrorMessage(
        timestamp="01/01/26-10:00:00:000",
        process_id=12345,
        severity=2,
        category="Utility.Event",
        message_text="LMF Error: No valid license key"
    )
    mocker.patch(
        'openai.OpenAI.beta.chat.completions.parse',
        return_value=MockResponse(parsed=mock_response)
    )
    
    # Test with mocked LLM
    agent = ErrorGeneratorAgent()
    result = agent.generate_error("license")
    assert result.category == "Utility.Event"
```

**Best Practices**:
- Write tests before implementation (TDD)
- Use fixtures for test data (logs, CPF files, commands)
- Mock all LLM calls in standard tests
- Separate suite for real LLM tests with budget limits
- Test error handling and rollback scenarios

---

## Summary of Key Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **Agent Framework** | OpenAI Agents SDK + Pydantic | Structured outputs, native LLM integration, educational value |
| **Communication** | String-based JSON in single process | Spec requirement, simplicity, debuggability |
| **Log Parsing** | LLM pattern extraction + regex fallback | Rich pattern learning, reliable fallback |
| **CPF Management** | configparser + LLM validation | Standard Python library, safe modification with rollback |
| **OS Operations** | subprocess with validation | Controlled execution, timeout handling, permission checks |
| **Logging** | structlog with JSON + contextvars | Structured output, trace ID propagation, observability |
| **Cost Control** | Token tracking + budget alerts + caching | Constitution compliance, cost effectiveness |
| **Testing** | Pytest + mocked LLM + fixtures | TDD support, predictable tests, real LLM tests separate |

---

## Implementation Priority

Based on user story priorities (P1-P6) from spec.md:

1. **Phase 1 (P1)**: Error message generation
   - Log parser for pattern extraction
   - ErrorGeneratorAgent with structured outputs
   - Message formatting and validation

2. **Phase 2 (P2)**: External message output
   - Message sender service (string-based interface)
   - Queue management for unreachable consumers
   - Delivery confirmation logging

3. **Phase 3 (P3)**: Remediation command reception
   - Command receiver service
   - JSON schema validation with Pydantic
   - Command queueing and conflict resolution

4. **Phase 4 (P4)**: IRIS configuration agent
   - CPF manager implementation
   - ConfigAgent with structured outputs
   - Restart requirement determination

5. **Phase 5 (P5)**: OS reconfiguration agent
   - OS command wrappers with validation
   - OSAgent with subprocess execution
   - Permission and availability checks

6. **Phase 6 (P6)**: Instance restart agent
   - Restart logic (graceful/forced)
   - RestartAgent with monitoring
   - Startup validation

---

## Next Steps

After research phase:
1. ✅ Create data-model.md defining all Pydantic models
2. ✅ Create contracts/ directory with JSON schemas
3. ✅ Create quickstart.md for getting started
4. ✅ Update agent context files
5. Begin implementation following TDD approach
