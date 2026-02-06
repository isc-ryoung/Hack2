"""CPF file manager for IRIS configuration management.

Handles reading, writing, and validating IRIS CPF (Configuration Parameter File) files.
"""

import configparser
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.utils.logger import get_logger


logger = get_logger(__name__)


class CPFManager:
    """Manager for IRIS CPF configuration files."""
    
    def __init__(self, cpf_path: Path):
        """Initialize CPF manager.
        
        Args:
            cpf_path: Path to iris.cpf file
        """
        self.cpf_path = Path(cpf_path)
        self.backup_dir = self.cpf_path.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def read_setting(self, section: str, key: str) -> Optional[str]:
        """Read a configuration setting from CPF file.
        
        Args:
            section: CPF section name
            key: Setting key
            
        Returns:
            Setting value or None if not found
        """
        try:
            config = configparser.ConfigParser()
            config.read(self.cpf_path)
            
            if config.has_option(section, key):
                value = config.get(section, key)
                logger.info(
                    "cpf_read_success",
                    section=section,
                    key=key,
                    value=value
                )
                return value
            else:
                logger.warning(
                    "cpf_setting_not_found",
                    section=section,
                    key=key
                )
                return None
        
        except Exception as e:
            logger.error(
                "cpf_read_failed",
                section=section,
                key=key,
                error=str(e)
            )
            return None
    
    def write_setting(
        self,
        section: str,
        key: str,
        value: str,
        create_backup: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """Write a configuration setting to CPF file.
        
        Args:
            section: CPF section name
            key: Setting key
            value: New setting value
            create_backup: Whether to create backup before modification
            
        Returns:
            Tuple of (success, backup_path)
        """
        backup_path = None
        
        try:
            # Create backup
            if create_backup:
                backup_path = self.create_backup()
                logger.info("cpf_backup_created", path=backup_path)
            
            # Read current config
            config = configparser.ConfigParser()
            config.read(self.cpf_path)
            
            # Get old value for logging
            old_value = None
            if config.has_option(section, key):
                old_value = config.get(section, key)
            
            # Ensure section exists
            if not config.has_section(section):
                config.add_section(section)
            
            # Set new value
            config.set(section, key, value)
            
            # Write to file
            with open(self.cpf_path, 'w') as f:
                config.write(f)
            
            logger.info(
                "cpf_write_success",
                section=section,
                key=key,
                old_value=old_value,
                new_value=value,
                backup_path=backup_path
            )
            
            return True, backup_path
        
        except Exception as e:
            logger.error(
                "cpf_write_failed",
                section=section,
                key=key,
                value=value,
                error=str(e)
            )
            
            # Attempt rollback if backup exists
            if backup_path:
                self.restore_backup(backup_path)
            
            return False, backup_path
    
    def create_backup(self) -> str:
        """Create backup of current CPF file.
        
        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"iris.cpf.backup.{timestamp}"
        
        shutil.copy2(self.cpf_path, backup_path)
        
        return str(backup_path)
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore CPF from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful
        """
        try:
            shutil.copy2(backup_path, self.cpf_path)
            logger.info("cpf_restore_success", backup_path=backup_path)
            return True
        except Exception as e:
            logger.error(
                "cpf_restore_failed",
                backup_path=backup_path,
                error=str(e)
            )
            return False
    
    def validate_cpf(self) -> bool:
        """Validate CPF file syntax.
        
        Returns:
            True if CPF is valid
        """
        try:
            config = configparser.ConfigParser()
            config.read(self.cpf_path)
            
            # Basic validation: ensure we can read it
            sections = config.sections()
            
            logger.info(
                "cpf_validation_success",
                sections_count=len(sections),
                sections=sections[:10]  # Log first 10 sections
            )
            return True
        
        except Exception as e:
            logger.error(
                "cpf_validation_failed",
                error=str(e)
            )
            return False
    
    def requires_restart(self, section: str, key: str) -> bool:
        """Determine if changing a setting requires IRIS restart.
        
        Args:
            section: CPF section name
            key: Setting key
            
        Returns:
            True if restart required
        """
        # Settings that always require restart
        restart_sections = {'Startup', 'config'}
        restart_keys = {
            'globals', 'routines', 'gmheap', 'locksiz',
            'genericheap', 'wijdir', 'database'
        }
        
        if section in restart_sections:
            logger.info(
                "restart_required_section",
                section=section,
                key=key,
                reason="Section always requires restart"
            )
            return True
        
        if key.lower() in restart_keys:
            logger.info(
                "restart_required_key",
                section=section,
                key=key,
                reason="Key changes require restart"
            )
            return True
        
        # Default: assume restart not required for safety
        logger.info(
            "restart_not_required",
            section=section,
            key=key
        )
        return False
    
    def get_all_sections(self) -> Dict[str, Dict[str, str]]:
        """Get all CPF sections and their settings.
        
        Returns:
            Dictionary mapping sections to their settings
        """
        try:
            config = configparser.ConfigParser()
            config.read(self.cpf_path)
            
            result = {}
            for section in config.sections():
                result[section] = dict(config.items(section))
            
            return result
        
        except Exception as e:
            logger.error(
                "cpf_read_all_failed",
                error=str(e)
            )
            return {}
