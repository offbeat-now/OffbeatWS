# utils/logger.py
import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from app.core.config import get_settings

class LoggerSetup:
    """Centralized logger configuration using loguru"""
    
    def __init__(self):
        self.settings = get_settings()
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure loguru logger based on settings"""
        # Remove default logger
        logger.remove()
        
        # Console logging
        logger.add(
            sys.stderr,
            level=self.settings.log_level,
            format=self._get_format(),
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
        
        # File logging
        if self.settings.log_file_enabled:
            log_path = Path(self.settings.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                str(log_path),
                level=self.settings.log_level,
                format=self._get_format(),
                rotation=self.settings.log_rotation,
                retention=self.settings.log_retention,
                compression="zip",
                backtrace=True,
                diagnose=True,
            )
    
    def _get_format(self) -> str:
        """Get log format based on configuration"""
        if self.settings.log_format == "simple":
            return "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        elif self.settings.log_format == "detailed":
            return (
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            )
        elif self.settings.log_format == "json":
            return (
                '{{'
                '"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
                '"level": "{level}", '
                '"logger": "{name}", '
                '"function": "{function}", '
                '"line": {line}, '
                '"message": "{message}"'
                '}}'
            )
        else:
            # Default format
            return (
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            )
    
    def get_logger(self, name: Optional[str] = None):
        """Get a logger instance"""
        if name:
            return logger.bind(name=name)
        return logger

# Global logger setup
logger_setup = LoggerSetup()
app_logger = logger_setup.get_logger("app")

# Convenience functions
def get_logger(name: str = "app"):
    """Get a named logger instance"""
    return logger_setup.get_logger(name)

# Standard logging adapter for libraries that use standard logging
class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru"""
    
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_standard_logging():
    """Setup standard logging to work with loguru"""
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    
    # Suppress some noisy loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)