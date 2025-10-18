"""
Advanced logging utilities
Provides structured logging, log analysis, and monitoring
"""
import logging
import os
import sys
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from app.config import settings


# ============================================
# Logging Setup
# ============================================

def setup_logging():
    """
    Setup application logging with proper formatting
    Configures both file and console handlers
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_FILE).parent
    if log_dir != Path('.'):
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(
        settings.LOG_FILE,
        encoding='utf-8',
        mode='a'
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # File formatter (detailed)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler (only in debug mode)
    if settings.DEBUG:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Console formatter (simpler)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Log startup message
    root_logger.info("=" * 50)
    root_logger.info("📝 Logging system initialized")
    root_logger.info(f"📁 Log file: {settings.LOG_FILE}")
    root_logger.info(f"📊 Log level: {settings.LOG_LEVEL}")
    root_logger.info("=" * 50)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# ============================================
# Log Analysis
# ============================================

class LogAnalyzer:
    """
    Analyze and parse log files
    Provides filtering, searching, and statistics
    """
    
    @staticmethod
    def read_logs(
        lines: int = 50,
        level: str = "all",
        search: str = ""
    ) -> Dict:
        """
        Read and filter log file
        
        Args:
            lines: Number of lines to return
            level: Log level filter (all, INFO, WARNING, ERROR)
            search: Search term to filter logs
            
        Returns:
            Dictionary with logs and statistics
        """
        if not os.path.exists(settings.LOG_FILE):
            return {
                "logs": "Log file not found. No logs generated yet.",
                "stats": {
                    "total_lines": 0,
                    "displayed_lines": 0,
                    "info_count": 0,
                    "warning_count": 0,
                    "error_count": 0
                }
            }
        
        try:
            with open(settings.LOG_FILE, "r", encoding="utf-8") as f:
                all_logs = f.readlines()
            
            # Initialize statistics
            stats = {
                "info_count": 0,
                "warning_count": 0,
                "error_count": 0
            }
            
            # Filter logs
            filtered_logs = []
            
            for log_line in all_logs:
                # Count by level (before filtering)
                if "INFO" in log_line:
                    stats["info_count"] += 1
                elif "WARNING" in log_line:
                    stats["warning_count"] += 1
                elif "ERROR" in log_line:
                    stats["error_count"] += 1
                
                # Level filter
                if level != "all" and level not in log_line:
                    continue
                
                # Search filter
                if search and search.lower() not in log_line.lower():
                    continue
                
                filtered_logs.append(log_line)
            
            # Limit results (get last N lines)
            displayed_logs = filtered_logs[-lines:] if lines > 0 else filtered_logs
            
            return {
                "logs": "".join(displayed_logs),
                "stats": {
                    "total_lines": len(all_logs),
                    "displayed_lines": len(displayed_logs),
                    **stats
                }
            }
            
        except Exception as e:
            logging.error(f"Error reading logs: {e}")
            return {
                "logs": f"Error reading logs: {str(e)}",
                "stats": {
                    "total_lines": 0,
                    "displayed_lines": 0,
                    "info_count": 0,
                    "warning_count": 0,
                    "error_count": 0
                }
            }
    
    @staticmethod
    def get_recent_errors(limit: int = 10) -> List[str]:
        """
        Get recent error messages from logs
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of error log lines
        """
        if not os.path.exists(settings.LOG_FILE):
            return []
        
        try:
            with open(settings.LOG_FILE, "r", encoding="utf-8") as f:
                all_logs = f.readlines()
            
            # Filter for errors
            errors = [line for line in all_logs if "ERROR" in line]
            
            # Return last N errors
            return errors[-limit:] if errors else []
            
        except Exception as e:
            logging.error(f"Error reading errors from log: {e}")
            return []
    
    @staticmethod
    def get_recent_warnings(limit: int = 10) -> List[str]:
        """
        Get recent warning messages from logs
        
        Args:
            limit: Maximum number of warnings to return
            
        Returns:
            List of warning log lines
        """
        if not os.path.exists(settings.LOG_FILE):
            return []
        
        try:
            with open(settings.LOG_FILE, "r", encoding="utf-8") as f:
                all_logs = f.readlines()
            
            # Filter for warnings
            warnings = [line for line in all_logs if "WARNING" in line]
            
            # Return last N warnings
            return warnings[-limit:] if warnings else []
            
        except Exception as e:
            logging.error(f"Error reading warnings from log: {e}")
            return []
    
    @staticmethod
    def clear_logs() -> bool:
        """
        Clear log file and reinitialize
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(settings.LOG_FILE):
                os.remove(settings.LOG_FILE)
            
            # Reinitialize logging
            setup_logging()
            logging.info("Log file cleared and reinitialized")
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to clear logs: {e}")
            return False
    
    @staticmethod
    def get_log_statistics() -> Dict:
        """
        Get comprehensive log statistics
        
        Returns:
            Dictionary with detailed statistics
        """
        if not os.path.exists(settings.LOG_FILE):
            return {
                "exists": False,
                "size_bytes": 0,
                "total_lines": 0
            }
        
        try:
            # Get file size
            file_size = os.path.getsize(settings.LOG_FILE)
            
            # Read all logs
            with open(settings.LOG_FILE, "r", encoding="utf-8") as f:
                all_logs = f.readlines()
            
            # Count by level
            info_count = sum(1 for line in all_logs if "INFO" in line)
            warning_count = sum(1 for line in all_logs if "WARNING" in line)
            error_count = sum(1 for line in all_logs if "ERROR" in line)
            debug_count = sum(1 for line in all_logs if "DEBUG" in line)
            
            # Get first and last log timestamps
            first_log = all_logs[0] if all_logs else None
            last_log = all_logs[-1] if all_logs else None
            
            return {
                "exists": True,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "total_lines": len(all_logs),
                "by_level": {
                    "INFO": info_count,
                    "WARNING": warning_count,
                    "ERROR": error_count,
                    "DEBUG": debug_count
                },
                "first_log": first_log.strip() if first_log else None,
                "last_log": last_log.strip() if last_log else None
            }
            
        except Exception as e:
            logging.error(f"Error getting log statistics: {e}")
            return {
                "exists": True,
                "error": str(e)
            }
    
    @staticmethod
    def search_logs(
        search_term: str,
        limit: int = 50,
        context_lines: int = 0
    ) -> List[str]:
        """
        Search logs for specific term with optional context
        
        Args:
            search_term: Term to search for
            limit: Maximum results
            context_lines: Number of lines before/after to include
            
        Returns:
            List of matching log lines (with context if requested)
        """
        if not os.path.exists(settings.LOG_FILE):
            return []
        
        try:
            with open(settings.LOG_FILE, "r", encoding="utf-8") as f:
                all_logs = f.readlines()
            
            matches = []
            search_lower = search_term.lower()
            
            for i, line in enumerate(all_logs):
                if search_lower in line.lower():
                    if context_lines > 0:
                        # Add context lines
                        start = max(0, i - context_lines)
                        end = min(len(all_logs), i + context_lines + 1)
                        context = all_logs[start:end]
                        matches.extend(context)
                    else:
                        matches.append(line)
                    
                    if len(matches) >= limit:
                        break
            
            return matches[:limit]
            
        except Exception as e:
            logging.error(f"Error searching logs: {e}")
            return []
    
    @staticmethod
    def get_logs_by_date(target_date: str) -> List[str]:
        """
        Get all logs for a specific date
        
        Args:
            target_date: Date in YYYY-MM-DD format
            
        Returns:
            List of log lines for that date
        """
        if not os.path.exists(settings.LOG_FILE):
            return []
        
        try:
            with open(settings.LOG_FILE, "r", encoding="utf-8") as f:
                all_logs = f.readlines()
            
            # Filter by date
            date_logs = [
                line for line in all_logs 
                if target_date in line
            ]
            
            return date_logs
            
        except Exception as e:
            logging.error(f"Error getting logs by date: {e}")
            return []


# ============================================
# Custom Log Handlers
# ============================================

class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output
    Makes logs more readable in terminal
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )
        
        return super().format(record)


# ============================================
# Logging Decorators
# ============================================

def log_function_call(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function calls
    
    Args:
        logger: Logger instance (optional)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)
            log.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                log.debug(f"{func.__name__} returned: {result}")
                return result
            except Exception as e:
                log.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        
        return wrapper
    return decorator


# ============================================
# Initialize logging on import
# ============================================

setup_logging()

# Create module logger
logger = get_logger(__name__)
logger.info("✅ Logging utilities loaded")
