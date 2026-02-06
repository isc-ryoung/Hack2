# Quick Start Guide: Instance - IRIS Operations Agent

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md) | **Data Model**: [data-model.md](data-model.md)  
**Created**: 2026-02-06  
**Purpose**: Get started with the Instance project quickly

## Overview

The **Instance** project is an Agentic AI system for simulating and remediating InterSystems IRIS database operational issues. This guide will help you:
1. Set up the development environment
2. Run your first error generation
3. Test remediation commands
4. Understand the agent architecture

---

## Prerequisites

- **Python 3.10+** (for pattern matching and modern type hints)
- **OpenAI API Key** (for LLM-powered agents)
- **Git** (for version control)
- **Linux Environment** (for OS operations; WSL2 on Windows)

---

## Installation

### 1. Clone and Setup

```bash
# Navigate to project root
cd /path/to/Hack2

# Create virtual environment
python3.10 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install openai pydantic>=2.0 structlog pytest pytest-mock pytest-asyncio python-dotenv
```

### 2. Configure Environment

```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-2024-08-06
LOG_LEVEL=INFO
TOKEN_BUDGET_PER_SESSION=5000
TOKEN_BUDGET_PER_DAY=500000
EOF
```

### 3. Verify Setup

```python
# test_setup.py
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4o-2024-08-06",
    messages=[{"role": "user", "content": "Say 'OK' if you can read this."}],
    max_tokens=10
)
print(f"Setup successful: {response.choices[0].message.content}")
```

Run: `python test_setup.py`

---

## Quick Start Examples

### Example 1: Generate an Error Message

This demonstrates the **ErrorGeneratorAgent** (User Story 1 - P1).

```python
from src.agents.error_generator import ErrorGeneratorAgent
from src.models.error_message import ErrorGenerationRequest

# Initialize agent
agent = ErrorGeneratorAgent()

# Create request for license error
request = ErrorGenerationRequest(
    error_category="license",
    severity=2
)

# Generate error
error_message = agent.generate_error(request)

# Output in IRIS log format
print(error_message.to_log_format())
# Output: 02/06/26-14:30:45:123 (12345) 2 [Utility.Event] LMF Error: No valid license key
```

### Example 2: Send Error to External System

This demonstrates **MessageSenderService** (User Story 2 - P2).

```python
from src.services.message_sender import MessageSenderService
from src.models.error_message import ErrorMessage

# Initialize service
sender = MessageSenderService(output_endpoint="http://external-system/api/messages")

# Create error message
error = ErrorMessage(
    timestamp="02/06/26-14:30:45:123",
    process_id=12345,
    severity=2,
    category="[Utility.Event]",
    message_text="LMF Error: No valid license key"
)

# Send to external system (returns delivery status)
status = sender.send_message(error)
print(f"Message sent: {status}")
```

### Example 3: Receive and Validate Command

This demonstrates **CommandReceiverService** (User Story 3 - P3).

```python
from src.services.command_receiver import CommandReceiverService
from src.models.remediation_command import RemediationCommand

# Initialize service
receiver = CommandReceiverService()

# Simulate receiving JSON command
command_json = """
{
    "action_type": "config_change",
    "target": "iris.cpf",
    "parameters": {
        "section": "Startup",
        "key": "globals",
        "value": "20000"
    },
    "priority": "high"
}
"""

# Parse and validate
try:
    command = RemediationCommand.model_validate_json(command_json)
    print(f"Valid command received: {command.action_type}")
    print(f"Target: {command.target}")
    print(f"Priority: {command.priority}")
except ValidationError as e:
    print(f"Invalid command: {e}")
```

### Example 4: Execute Configuration Change

This demonstrates **ConfigAgent** (User Story 4 - P4).

```python
from src.agents.config_agent import ConfigAgent
from src.models.remediation_command import RemediationCommand

# Initialize agent
agent = ConfigAgent(cpf_path="/usr/local/IRIS/iris.cpf")

# Create config change command
command = RemediationCommand(
    action_type="config_change",
    target="iris.cpf",
    parameters={
        "section": "Startup",
        "key": "globals",
        "value": "20000"
    },
    priority="high"
)

# Execute change (returns ConfigAgentResponse as JSON string)
response_str = agent.execute(command.model_dump_json())

# Parse response
from src.models.agent_responses import ConfigAgentResponse
response = ConfigAgentResponse.model_validate_json(response_str)

print(f"Success: {response.success}")
print(f"Old value: {response.old_value}")
print(f"New value: {response.new_value}")
print(f"Requires restart: {response.requires_restart}")
```

### Example 5: Full Remediation Workflow

This demonstrates the complete orchestration flow.

```python
from src.agents.orchestrator import OrchestratorAgent
from src.agents.config_agent import ConfigAgent
from src.models.remediation_command import RemediationCommand
from src.models.execution_context import ExecutionContext
from uuid import uuid4

# Initialize components
orchestrator = OrchestratorAgent()
config_agent = ConfigAgent()
context = ExecutionContext(
    trace_id=uuid4(),
    command_id=uuid4()
)

# 1. Receive command
command_json = """
{
    "action_type": "config_change",
    "target": "iris.cpf",
    "parameters": {
        "section": "Startup",
        "key": "globals",
        "value": "20000"
    },
    "priority": "high"
}
"""
command = RemediationCommand.model_validate_json(command_json)

# 2. Orchestrator analyzes and routes
orchestrator_response_str = orchestrator.analyze_command(command.model_dump_json())
orchestrator_response = OrchestratorResponse.model_validate_json(orchestrator_response_str)

print(f"Selected agent: {orchestrator_response.agent_type}")
print(f"Rationale: {orchestrator_response.rationale}")
print(f"Risk level: {orchestrator_response.estimated_risk}")

# 3. Execute with selected agent
if orchestrator_response.agent_type == "config":
    result_str = config_agent.execute(orchestrator_response.command_str)
    result = ConfigAgentResponse.model_validate_json(result_str)
    
    # 4. Update execution context
    context.add_agent_result(
        agent_name="config_agent",
        result_json=result_str,
        tokens=450,  # Example token count
        cost=0.0067  # Example cost
    )

print(f"Total tokens used: {context.total_tokens_used}")
print(f"Total cost: ${context.total_cost_usd:.4f}")
print(f"Duration: {context.duration_seconds:.2f}s")
```

---

## Notebook Tutorials

The project includes interactive Jupyter notebooks for learning:

### Getting Started Notebooks

1. **Introduction to Agents** (`notebooks/tutorials/01_introduction_to_agents.ipynb`)
   - Agent architecture overview
   - String-based communication pattern
   - Structured outputs with Pydantic

2. **Building Custom Agents** (`notebooks/tutorials/02_building_custom_agents.ipynb`)
   - Create your own agent
   - Implement structured responses
   - Add observability and logging

3. **Agent Testing Patterns** (`notebooks/tutorials/03_agent_testing_patterns.ipynb`)
   - TDD approach for agents
   - Mocking LLM responses
   - Integration testing strategies

### Demo Notebooks

1. **Error Generation Demo** (`notebooks/demos/01_error_generation_demo.ipynb`)
   - Generate various error types
   - Parse IRIS logs for patterns
   - Output formatting

2. **Remediation Workflow Demo** (`notebooks/demos/02_remediation_workflow_demo.ipynb`)
   - End-to-end remediation flow
   - Command validation
   - Agent orchestration

3. **Agent Orchestration Demo** (`notebooks/demos/03_agent_orchestration_demo.ipynb`)
   - Multi-agent workflows
   - Error handling and rollback
   - Cost tracking

### Running Notebooks

```bash
# Install Jupyter
pip install jupyter

# Start Jupyter Lab
jupyter lab

# Navigate to notebooks/ directory
# Open any .ipynb file
```

---

## Project Structure

```
.
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── error_generator.py
│   │   ├── orchestrator.py
│   │   ├── config_agent.py
│   │   ├── os_agent.py
│   │   └── restart_agent.py
│   ├── models/              # Pydantic data models
│   │   ├── error_message.py
│   │   ├── remediation_command.py
│   │   ├── agent_responses.py
│   │   └── execution_context.py
│   ├── services/            # Business logic
│   │   ├── log_parser.py
│   │   ├── message_sender.py
│   │   ├── command_receiver.py
│   │   └── cpf_manager.py
│   ├── prompts/             # Prompt templates
│   └── utils/               # Logging, cost tracking
│
├── notebooks/               # Jupyter notebooks
│   ├── demos/
│   ├── experiments/
│   └── tutorials/
│
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── prompts/
│
├── log_samples/             # Sample IRIS logs
│   └── messages.log
│
└── specs/001-iris-ops-agent/  # Documentation
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md (this file)
    └── contracts/
```

---

## Development Workflow

### 1. Notebook-First Development

Per the Agentic AI Workshop Constitution:

1. **Explore in notebooks**: Start in `notebooks/experiments/`
2. **Prototype agents**: Test ideas with minimal code
3. **Extract to src/**: Move working code to `src/agents/`
4. **Add tests**: Write tests in `tests/`
5. **Document**: Update docstrings and examples

### 2. Test-Driven Development

Follow TDD for all agent logic:

```bash
# 1. Write failing test
# tests/unit/test_log_parser.py
def test_parse_error_line():
    parser = LogParser()
    line = "02/06/26-14:30:45:123 (12345) 2 [Utility.Event] Error message"
    result = parser.parse_line(line)
    assert result.severity == 2

# 2. Run test (should fail)
pytest tests/unit/test_log_parser.py

# 3. Implement feature
# src/services/log_parser.py
class LogParser:
    def parse_line(self, line: str) -> ErrorMessage:
        # Implementation...

# 4. Run test (should pass)
pytest tests/unit/test_log_parser.py
```

### 3. Observability

All operations are logged with structured logging:

```python
import structlog
from src.utils.logger import configure_logging

configure_logging()
log = structlog.get_logger()

# Automatic trace ID from context
log.info("operation_start", operation="error_generation", category="license")
# ... perform operation ...
log.info("operation_complete", tokens_used=450, cost_usd=0.0067)
```

View logs:
```bash
# Logs are written to stdout in JSON format
python your_script.py | jq .

# Filter by trace_id
python your_script.py | jq 'select(.trace_id == "550e8400-e29b-41d4-a716-446655440000")'
```

---

## Common Tasks

### Generate Sample Errors

```bash
# Generate 10 random errors
python -m src.cli.generate_errors --count 10 --output errors.log

# Generate specific error type
python -m src.cli.generate_errors --category license --severity 2
```

### Test Remediation Command

```bash
# Send test command
python -m src.cli.send_command --file tests/fixtures/sample_commands.json

# Validate command format
python -m src.cli.validate_command --file my_command.json
```

### Monitor Cost

```bash
# Check current session costs
python -m src.cli.cost_report --session

# Check daily usage
python -m src.cli.cost_report --daily
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/integration/test_error_generator_agent.py

# Run with verbose output
pytest -v

# Run real LLM tests (requires budget)
pytest tests/integration/ -m "real_llm"
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'openai'"

**Solution**: Activate virtual environment and install dependencies
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: "OpenAI API authentication error"

**Solution**: Check .env file has valid API key
```bash
cat .env | grep OPENAI_API_KEY
# Should show: OPENAI_API_KEY=sk-...
```

### Issue: "Token budget exceeded"

**Solution**: Adjust budget in .env or use gpt-3.5-turbo
```bash
# Increase budget
export TOKEN_BUDGET_PER_SESSION=10000

# Use cheaper model
export OPENAI_MODEL=gpt-3.5-turbo
```

### Issue: "Permission denied when modifying CPF file"

**Solution**: Run with appropriate permissions or use test mode
```python
# Use test mode (no actual file changes)
agent = ConfigAgent(test_mode=True)
```

---

## Next Steps

1. **Complete Tutorial Notebooks**: Work through all 3 tutorial notebooks
2. **Run Demo Notebooks**: Explore the 3 demo notebooks
3. **Read Research Document**: Understand technology decisions in [research.md](research.md)
4. **Review Data Models**: Study Pydantic models in [data-model.md](data-model.md)
5. **Contribute**: Follow the development workflow to add features

---

## Resources

- **Specification**: [spec.md](spec.md) - Feature requirements and user stories
- **Implementation Plan**: [plan.md](plan.md) - Technical approach and architecture
- **Research**: [research.md](research.md) - Technology decisions and patterns
- **Data Model**: [data-model.md](data-model.md) - Pydantic models and schemas
- **Contracts**: [contracts/](contracts/) - JSON schemas for interfaces

**External Documentation**:
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [InterSystems IRIS Documentation](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls)

---

## Support

For questions or issues:
1. Check troubleshooting section above
2. Review [research.md](research.md) for design decisions
3. Search [spec.md](spec.md) for requirements clarification
4. Open an issue in the project repository

**Happy coding! 🚀**
