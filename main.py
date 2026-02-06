#!/usr/bin/env python
"""CLI entry point for Instance - IRIS Operations Agent.

Provides command-line access to all agent operations.
"""

import argparse
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.error_generator_sdk import ErrorGeneratorAgentSDK
from src.agents.orchestrator_sdk import OrchestratorAgentSDK
from src.agents.config_agent_sdk import ConfigAgentSDK
from src.agents.os_agent_sdk import OSAgentSDK
from src.agents.restart_agent_sdk import RestartAgentSDK
from src.models.error_message import ErrorGenerationRequest
from src.models.remediation_command import RemediationCommand
from src.utils.logger import get_logger


logger = get_logger(__name__)


def cmd_generate_error(args):
    """Generate an IRIS error message."""
    print("🔧 Generating IRIS error message...")
    
    # Initialize agent
    log_path = Path(args.log_samples) if args.log_samples else None
    agent = ErrorGeneratorAgentSDK(log_samples_path=log_path)
    
    # Create request
    request = ErrorGenerationRequest(
        error_category=args.category,
        severity=args.severity
    )
    
    # Generate error
    error = agent.generate_error(request)
    
    # Output
    print(f"\n✅ Generated error:")
    print(f"   {error.to_log_format()}")
    
    if args.json:
        print(f"\n📄 JSON output:")
        print(error.model_dump_json(indent=2))


def cmd_route_command(args):
    """Route a remediation command to appropriate agent."""
    print("🔀 Routing remediation command...")
    
    # Load command from file or CLI args
    if args.file:
        with open(args.file, 'r') as f:
            command_data = json.load(f)
        command = RemediationCommand(**command_data)
    else:
        command = RemediationCommand(
            action_type=args.action,
            target=args.target,
            parameters=json.loads(args.parameters) if args.parameters else {}
        )
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgentSDK()
    
    # Route command
    response = orchestrator.route_command(command)
    
    # Output
    print(f"\n✅ Routing decision:")
    print(f"   Agent: {response.agent_type}")
    print(f"   Risk: {response.estimated_risk}")
    print(f"   Validation Required: {response.requires_validation}")
    print(f"   Rationale: {response.rationale}")
    
    if args.json:
        print(f"\n📄 JSON output:")
        print(response.model_dump_json(indent=2))


def cmd_config_change(args):
    """Execute a configuration change."""
    print("⚙️  Executing configuration change...")
    
    # Initialize agent
    cpf_path = Path(args.cpf_path) if args.cpf_path else None
    agent = ConfigAgentSDK(cpf_path=cpf_path)
    
    # Execute change
    response = agent.modify_config(
        section=args.section,
        key=args.key,
        value=args.value
    )
    
    # Output
    if response.success:
        print(f"\n✅ Configuration changed successfully:")
        print(f"   Section: {response.section}")
        print(f"   Key: {response.key}")
        print(f"   Old Value: {response.old_value}")
        print(f"   New Value: {response.new_value}")
        print(f"   Restart Required: {response.requires_restart}")
        if response.backup_path:
            print(f"   Backup: {response.backup_path}")
    else:
        print(f"\n❌ Configuration change failed:")
        print(f"   Error: {response.error_message}")
        sys.exit(1)
    
    if args.json:
        print(f"\n📄 JSON output:")
        print(response.model_dump_json(indent=2))


def cmd_os_reconfig(args):
    """Execute OS resource reconfiguration."""
    print("💾 Executing OS reconfiguration...")
    
    # Initialize agent
    agent = OSAgentSDK()
    
    # Execute reconfiguration
    response = agent.reconfigure_resource(
        resource_type=args.resource,
        target_value=args.value
    )
    
    # Output
    if response.success:
        print(f"\n✅ OS reconfiguration successful:")
        print(f"   Resource: {response.resource_type}")
        print(f"   Old Value: {response.old_value}")
        print(f"   New Value: {response.new_value}")
        print(f"   Validation Passed: {response.validation_passed}")
        if response.commands_executed:
            print(f"   Commands:")
            for cmd in response.commands_executed:
                print(f"      - {cmd}")
    else:
        print(f"\n❌ OS reconfiguration failed:")
        print(f"   Error: {response.error_message}")
        sys.exit(1)
    
    if args.json:
        print(f"\n📄 JSON output:")
        print(response.model_dump_json(indent=2))


def cmd_restart(args):
    """Execute IRIS instance restart."""
    print("🔄 Executing IRIS instance restart...")
    
    # Confirm if forced
    if args.mode == "forced":
        confirm = input("⚠️  Forced restart will cause immediate downtime. Continue? [y/N]: ")
        if confirm.lower() != 'y':
            print("Restart cancelled.")
            return
    
    # Initialize agent
    agent = RestartAgentSDK(iris_instance=args.instance)
    
    # Execute restart
    response = agent.restart_instance(
        mode=args.mode,
        timeout_seconds=args.timeout
    )
    
    # Output
    if response.success:
        print(f"\n✅ Restart completed successfully:")
        print(f"   Mode: {response.mode}")
        print(f"   Connections Drained: {response.connections_drained}")
        print(f"   Shutdown Duration: {response.shutdown_duration_seconds}s")
        print(f"   Startup Duration: {response.startup_duration_seconds}s")
        print(f"   Operational Status: {response.operational_status}")
    else:
        print(f"\n❌ Restart failed:")
        print(f"   Status: {response.operational_status}")
        print(f"   Error: {response.error_message}")
        sys.exit(1)
    
    if args.json:
        print(f"\n📄 JSON output:")
        print(response.model_dump_json(indent=2))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Instance - IRIS Operations Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a license error
  python main.py generate-error --category license --severity 2
  
  # Route a command from JSON file
  python main.py route-command --file command.json
  
  # Change CPF configuration
  python main.py config-change --section Startup --key globals --value 20000
  
  # Reconfigure memory
  python main.py os-reconfig --resource memory --value 16384
  
  # Perform graceful restart
  python main.py restart --mode graceful --timeout 60
        """
    )
    
    parser.add_argument('--json', action='store_true', help='Output JSON response')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Generate error command
    gen_parser = subparsers.add_parser('generate-error', help='Generate IRIS error message')
    gen_parser.add_argument('--category', required=True, 
                           choices=['license', 'config', 'os', 'journal', 'other'],
                           help='Error category')
    gen_parser.add_argument('--severity', type=int, default=2, choices=[0, 1, 2, 3],
                           help='Severity level (0=info, 1=warning, 2=error, 3=fatal)')
    gen_parser.add_argument('--log-samples', help='Path to log samples file')
    gen_parser.set_defaults(func=cmd_generate_error)
    
    # Route command
    route_parser = subparsers.add_parser('route-command', help='Route remediation command')
    route_parser.add_argument('--file', help='JSON file with command data')
    route_parser.add_argument('--action', help='Action type (config_change, os_reconfig, restart)')
    route_parser.add_argument('--target', help='Target resource')
    route_parser.add_argument('--parameters', help='JSON string with parameters')
    route_parser.set_defaults(func=cmd_route_command)
    
    # Config change command
    config_parser = subparsers.add_parser('config-change', help='Execute configuration change')
    config_parser.add_argument('--section', required=True, help='CPF section')
    config_parser.add_argument('--key', required=True, help='Configuration key')
    config_parser.add_argument('--value', required=True, help='New value')
    config_parser.add_argument('--cpf-path', help='Path to iris.cpf file')
    config_parser.set_defaults(func=cmd_config_change)
    
    # OS reconfiguration command
    os_parser = subparsers.add_parser('os-reconfig', help='Execute OS reconfiguration')
    os_parser.add_argument('--resource', required=True, choices=['memory', 'cpu'],
                          help='Resource type')
    os_parser.add_argument('--value', type=int, required=True,
                          help='Target value (MB for memory, cores for CPU)')
    os_parser.set_defaults(func=cmd_os_reconfig)
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Execute IRIS instance restart')
    restart_parser.add_argument('--mode', default='graceful', choices=['graceful', 'forced'],
                               help='Restart mode')
    restart_parser.add_argument('--timeout', type=int, default=60,
                               help='Timeout in seconds for graceful shutdown')
    restart_parser.add_argument('--instance', default='IRIS', help='IRIS instance name')
    restart_parser.set_defaults(func=cmd_restart)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error("cli_error", error=str(e), exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
