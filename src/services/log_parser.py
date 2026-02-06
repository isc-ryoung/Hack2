"""Log parser service for extracting patterns from IRIS messages.log.

Parses log files to extract error patterns for realistic error generation.
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from src.models.error_message import ErrorMessage
from src.utils.logger import get_logger


logger = get_logger(__name__)


class LogParser:
    """Parser for IRIS messages.log files."""
    
    # IRIS log format: MM/DD/YY-HH:MM:SS:mmm (PID) Severity [Category] Message
    LOG_PATTERN = re.compile(
        r'(\d{2}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}:\d{3})\s+'  # timestamp
        r'\((\d+)\)\s+'  # process ID
        r'(\d)\s+'  # severity
        r'(\[[\w\.]+\])\s+'  # category
        r'(.+)$'  # message text
    )
    
    def __init__(self, log_file_path: Optional[Path] = None):
        """Initialize log parser.
        
        Args:
            log_file_path: Path to messages.log file
        """
        self.log_file_path = log_file_path
        self.patterns: Dict[str, List[ErrorMessage]] = defaultdict(list)
        self.total_entries = 0
    
    def parse_log_file(self, log_file_path: Optional[Path] = None) -> Dict[str, List[ErrorMessage]]:
        """Parse log file and extract error patterns.
        
        Args:
            log_file_path: Path to log file (overrides instance path)
            
        Returns:
            Dictionary mapping error categories to lists of ErrorMessage objects
        """
        file_path = log_file_path or self.log_file_path
        
        if not file_path or not Path(file_path).exists():
            logger.warning(
                "log_file_not_found",
                path=str(file_path),
                message="Log file not found, using empty patterns"
            )
            return self.patterns
        
        logger.info("log_parsing_start", path=str(file_path))
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    entry = self.parse_line(line)
                    if entry:
                        self.total_entries += 1
                        category = self._categorize_error(entry)
                        self.patterns[category].append(entry)
            
            logger.info(
                "log_parsing_complete",
                path=str(file_path),
                total_entries=self.total_entries,
                categories=list(self.patterns.keys()),
                category_counts={k: len(v) for k, v in self.patterns.items()}
            )
        
        except Exception as e:
            logger.error(
                "log_parsing_failed",
                path=str(file_path),
                error=str(e)
            )
        
        return self.patterns
    
    def parse_line(self, line: str) -> Optional[ErrorMessage]:
        """Parse a single log line into ErrorMessage.
        
        Args:
            line: Log line text
            
        Returns:
            ErrorMessage object or None if parsing fails
        """
        match = self.LOG_PATTERN.match(line)
        if not match:
            return None
        
        try:
            timestamp, pid, severity, category, message = match.groups()
            
            return ErrorMessage(
                timestamp=timestamp,
                process_id=int(pid),
                severity=int(severity),
                category=category,
                message_text=message.strip()
            )
        except Exception as e:
            logger.debug(
                "log_line_parse_failed",
                line=line[:100],
                error=str(e)
            )
            return None
    
    def _categorize_error(self, entry: ErrorMessage) -> str:
        """Categorize error into standard types.
        
        Args:
            entry: Parsed error message
            
        Returns:
            Category string (config, license, os, journal, other)
        """
        message_lower = entry.message_text.lower()
        
        # License errors
        if any(keyword in message_lower for keyword in ['license', 'lmf', 'key']):
            return 'license'
        
        # Configuration errors
        if any(keyword in message_lower for keyword in [
            'config', 'parameter', 'startup', 'globals', 'routines', 'cpf'
        ]):
            return 'config'
        
        # OS resource errors
        if any(keyword in message_lower for keyword in [
            'memory', 'allocation', 'shared memory', 'buffer', 'cpu', 'resource'
        ]):
            return 'os'
        
        # Journal errors
        if any(keyword in message_lower for keyword in [
            'journal', 'wij', 'write-image', 'lock'
        ]):
            return 'journal'
        
        return 'other'
    
    def get_examples(self, category: str, count: int = 5) -> List[ErrorMessage]:
        """Get example error messages for a category.
        
        Args:
            category: Error category
            count: Number of examples to return
            
        Returns:
            List of ErrorMessage objects
        """
        return self.patterns.get(category, [])[:count]
    
    def get_all_categories(self) -> List[str]:
        """Get all available error categories.
        
        Returns:
            List of category names
        """
        return list(self.patterns.keys())
