"""
Logging configuration for Senthium
Provides colored console output and file logging with rotation
"""

import logging
import logging.handlers
import os
from pathlib import Path
import colorlog

# Default log directory
DEFAULT_LOG_DIR = Path(__file__).parent.parent.parent / 'logs'
DEFAULT_LOG_FILE = 'senthium.log'


def setup_logger(
    name: str = 'senthium',
    level: str = 'INFO',
    log_to_file: bool = True,
    log_dir: Path = DEFAULT_LOG_DIR,
    log_file: str = DEFAULT_LOG_FILE
) -> logging.Logger:
    """
    Set up logger with colored console output and optional file logging
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_dir: Directory for log files
        log_file: Log file name
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Keep propagation enabled so test capture (caplog) can observe records.
    # We rely on using unique logger names and delayed file opening to
    # avoid accidental double-handling and file lock issues.
    
    # Console handler with colors
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setStream(open(1, 'w', encoding='utf-8', closefd=False))  # UTF-8 stdout
    
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file:
        # Create log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_path = log_dir / log_file
        # Use delay=True to avoid opening the file until the first emit.
        # This reduces the window where the file is held open and helps
        # on Windows when tests create/remove temporary directories.
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            delay=True,
            encoding='utf-8'  # UTF-8 encoding for emoji support
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Example usage (for testing)
if __name__ == '__main__':
    logger = setup_logger('test', level='DEBUG')
    logger.debug("This is a debug message 🐛")
    logger.info("This is an info message ℹ️")
    logger.warning("This is a warning message ⚠️")
    logger.error("This is an error message ❌")
    logger.critical("This is a critical message 🔥")
