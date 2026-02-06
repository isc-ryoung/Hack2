# Instance - IRIS Operations Agent

An Agentic AI system for simulating and remediating InterSystems IRIS database operational issues.

## Overview

**Instance** is an intelligent automation platform that:
- **Generates** realistic IRIS error messages based on patterns from actual logs
- **Transmits** simulated errors to external monitoring systems
- **Receives** JSON remediation commands from external sources
- **Executes** automated remediation through specialized AI agents

### Agents

- **ErrorGeneratorAgent**: Generates IRIS error messages (config, license, OS, journal errors)
- **OrchestratorAgent**: Routes remediation commands to appropriate specialized agents
- **ConfigAgent**: Modifies IRIS CPF configuration files
- **OSAgent**: Adjusts operating system memory and CPU settings
- **RestartAgent**: Manages IRIS instance restart operations

## Prerequisites

- **Python 3.10+** (for pattern matching and modern type hints)
- **OpenAI API Key** (for LLM-powered agents)
- **Linux Environment** (for OS operations; WSL2 on Windows)

## Installation

### 1. Clone and Setup

```bash
# Navigate to project root
cd C:\tmp\Hack2

# Create virtual environment
python3.10 -m venv .venv

# Activate virtual environment
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# - Add your OpenAI API key
# - Configure endpoints for external systems
# - Set IRIS installation paths
```

### 3. Verify Installation

```bash
# Run tests to verify setup
pytest tests/

# Check Python version
python --version  # Should be 3.10 or higher
```

## Quick Start

### CLI Interface (Recommended) 🚀

The easiest way to use the system is through the command-line interface:

```bash
# Generate an error message
python main.py generate-error --category license --severity 2

# Route a remediation command
python main.py route-command --action config_change --target iris.cpf \
    --parameters '{"section":"Startup","key":"globals","value":"20000"}'

# Execute a configuration change
python main.py config-change --section Startup --key globals --value 20000

# Reconfigure OS memory
python main.py os-reconfig --resource memory --value 16384

# Restart IRIS instance
python main.py restart --mode graceful --timeout 60

# Get JSON output
python main.py generate-error --category license --severity 2 --json
```

**Available Commands:**
- `generate-error`: Generate IRIS error messages
- `route-command`: Route remediation commands to agents
- `config-change`: Modify IRIS CPF configuration
- `os-reconfig`: Reconfigure OS resources (memory, CPU)
- `restart`: Restart IRIS instance (graceful or forced)

Run `python main.py --help` or `python main.py <command> --help` for detailed options.

### Quick Reference

| Task | Command |
|------|---------|
| Generate error | `python main.py generate-error --category license --severity 2` |
| Route from file | `python main.py route-command --file example_command.json` |
| Change config | `python main.py config-change --section Startup --key globals --value 20000` |
| JSON output | `python main.py --json generate-error --category license --severity 2` |

See [example_command.json](example_command.json) for a sample command file.

### Python API

You can also use the agents directly in your Python code:

```python
from src.agents.error_generator_sdk import ErrorGeneratorAgentSDK
from src.models.error_message import ErrorGenerationRequest

# Initialize agent
agent = ErrorGeneratorAgentSDK()

# Generate a license error
request = ErrorGenerationRequest(
    error_category="license",
    severity=2
)
error = agent.generate_error(request)

# Output in IRIS log format
print(error.to_log_format())
# Output: 02/06/26-14:30:45:123 (12345) 2 [Utility.Event] LMF Error: No valid license key
```

### Execute Configuration Change

```python
from src.agents.config_agent_sdk import ConfigAgentSDK
from src.models.remediation_command import RemediationCommand

# Initialize agent
agent = ConfigAgentSDK(cpf_path="/usr/irissys/iris.cpf")

# Create config change command
command = RemediationCommand(
    action_type="config_change",
    target="iris.cpf",
    parameters={
        "section": "Startup",
        "key": "globals",
        "value": "20000"
    }
)

# Execute change
response_str = agent.execute(command.model_dump_json())
print(response_str)
```

## Project Structure

```
.
├── src/
│   ├── agents/          # Agent implementations
│   ├── models/          # Pydantic data models
│   ├── services/        # External integrations
│   ├── prompts/         # LLM prompt templates
│   └── utils/           # Logging, cost tracking, config
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   ├── prompts/         # Prompt regression tests
│   ├── fixtures/        # Test data
│   └── contract/        # Contract tests
├── notebooks/
│   ├── demos/           # Workshop demonstrations
│   ├── experiments/     # Prototyping notebooks
│   └── tutorials/       # Learning materials
├── log_samples/         # Sample IRIS messages.log files
└── specs/               # Feature specifications
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/                  # Unit tests only
pytest tests/integration/           # Integration tests only
pytest tests/prompts/               # Prompt regression tests

# Run with coverage
pytest --cov=src --cov-report=html

# Run with verbose output
pytest -v
```

### Notebooks

Explore the system through Jupyter notebooks:

```bash
# Start Jupyter
jupyter lab

# Navigate to notebooks/demos/ for demonstrations
# Navigate to notebooks/tutorials/ for learning materials
```

### Code Style

```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Type checking
mypy src/
```

## Architecture

### Communication Flow

1. **Error Generation**: `ErrorGeneratorAgent` → Creates IRIS error messages → `MessageSenderService` → External system
2. **Command Reception**: External system → `CommandReceiverService` → Validates JSON → `OrchestratorAgent`
3. **Agent Routing**: `OrchestratorAgent` → Selects agent → Routes command (string-based JSON)
4. **Remediation**: `ConfigAgent`/`OSAgent`/`RestartAgent` → Executes action → Returns result

### Key Principles

- **Test-Driven**: All agents have comprehensive test coverage with mocked LLM responses
- **Observable**: Structured logging with trace IDs for all operations
- **Cost-Conscious**: Token tracking and budget alerts prevent runaway costs
- **Educational**: Extensive documentation and notebooks for learning

## Configuration

Key settings in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM access | Required |
| `OPENAI_MODEL` | Primary model for structured outputs | `gpt-4o-2024-08-06` |
| `TOKEN_BUDGET_PER_WORKFLOW` | Max tokens per remediation workflow | `5000` |
| `IRIS_CPF_PATH` | Path to IRIS configuration file | `/usr/irissys/iris.cpf` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

See [.env.example](.env.example) for full configuration options.

## Documentation

- [Feature Specification](specs/001-iris-ops-agent/spec.md) - User stories and requirements
- [Implementation Plan](specs/001-iris-ops-agent/plan.md) - Technical architecture
- [Data Model](specs/001-iris-ops-agent/data-model.md) - Pydantic entity definitions
- [Research](specs/001-iris-ops-agent/research.md) - Technology decisions
- [Quick Start Guide](specs/001-iris-ops-agent/quickstart.md) - Detailed examples

## Workshop Materials

This project serves as an educational platform for Agentic AI patterns:

- **Tutorial Notebooks**: Step-by-step introductions to agent concepts
- **Demo Notebooks**: Working examples of each agent
- **Experiment Notebooks**: Prototyping and exploration

## Troubleshooting

### Common Issues

**ModuleNotFoundError**:
```bash
# Ensure virtual environment is activated
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/macOS

# Reinstall dependencies
pip install -r requirements.txt
```

**OpenAI API Errors**:
```bash
# Verify API key in .env file
cat .env | grep OPENAI_API_KEY

# Test API access
python -c "from openai import OpenAI; client = OpenAI(); print('OK')"
```

**Test Failures**:
```bash
# Run with verbose output to see details
pytest -v -s

# Check specific test
pytest tests/unit/test_logger.py -v
```

## Contributing

This project follows the Agentic AI Workshop Constitution:
1. **Agent-First Design**: Each agent has single responsibility
2. **Notebook-Driven**: Prototype in notebooks, extract to src/
3. **Test-Driven AI**: Write tests first, ensure they fail
4. **Observability**: Log all LLM calls with trace IDs
5. **Cost Management**: Track tokens and enforce budgets
6. **Educational Clarity**: Extensive documentation and examples

## License

MIT License - See [LICENSE](LICENSE) for details

## Support

- **Specification**: [specs/001-iris-ops-agent/](specs/001-iris-ops-agent/)
- **Issues**: File issues in the repository issue tracker
- **Documentation**: See [quickstart.md](specs/001-iris-ops-agent/quickstart.md) for detailed examples

---

**Status**: 🚧 Development Phase  
**Branch**: `001-iris-ops-agent`  
**Last Updated**: 2026-02-06
