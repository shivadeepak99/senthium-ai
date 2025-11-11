"""
Unit tests for Logger utility
"""

import pytest
import logging
from pathlib import Path
from src.utils.logger import setup_logger
import tempfile
import os


class TestLogger:
    """Test suite for logger utility"""
    
    def test_logger_creation(self):
        """Test that logger can be created"""
        logger = setup_logger('test_logger', level='INFO', log_to_file=False)
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_logger'
        assert logger.level == logging.INFO
    
    def test_logger_level_debug(self):
        """Test logger with DEBUG level"""
        logger = setup_logger('test_debug', level='DEBUG', log_to_file=False)
        assert logger.level == logging.DEBUG
    
    def test_logger_level_warning(self):
        """Test logger with WARNING level"""
        logger = setup_logger('test_warning', level='WARNING', log_to_file=False)
        assert logger.level == logging.WARNING
    
    def test_logger_level_error(self):
        """Test logger with ERROR level"""
        logger = setup_logger('test_error', level='ERROR', log_to_file=False)
        assert logger.level == logging.ERROR
    
    def test_logger_level_critical(self):
        """Test logger with CRITICAL level"""
        logger = setup_logger('test_critical', level='CRITICAL', log_to_file=False)
        assert logger.level == logging.CRITICAL
    
    def test_logger_with_file_logging(self):
        """Test logger writes to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = 'test.log'
            
            logger = setup_logger(
                'test_file_logger',
                level='INFO',
                log_to_file=True,
                log_dir=log_dir,
                log_file=log_file
            )
            
            # Write test message
            logger.info("Test message")
            
            # Close all handlers to release file lock (Windows fix)
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            
            # Check file was created
            log_path = log_dir / log_file
            assert log_path.exists()
            
            # Check message was written
            with open(log_path, 'r') as f:
                content = f.read()
                assert "Test message" in content
                assert "INFO" in content
    
    def test_logger_creates_directory(self):
        """Test that logger creates log directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'new_logs' / 'subdir'
            
            logger = setup_logger(
                'test_dir_creation',
                level='INFO',
                log_to_file=True,
                log_dir=log_dir,
                log_file='test.log'
            )
            
            logger.info("Test")
            
            # Close all handlers to release file lock (Windows fix)
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            
            # Check directory was created
            assert log_dir.exists()
            assert log_dir.is_dir()
    
    def test_logger_no_duplicate_handlers(self):
        """Test that calling setup_logger twice doesn't add duplicate handlers"""
        logger1 = setup_logger('test_duplicate', level='INFO', log_to_file=False)
        handler_count1 = len(logger1.handlers)
        
        logger2 = setup_logger('test_duplicate', level='INFO', log_to_file=False)
        handler_count2 = len(logger2.handlers)
        
        # Should return same logger with same handlers
        assert logger1 is logger2
        assert handler_count1 == handler_count2
    
    def test_logger_console_output(self, caplog):
        """Test that logger outputs to console"""
        logger = setup_logger('test_console', level='INFO', log_to_file=False)
        
        with caplog.at_level(logging.INFO):
            logger.info("Console test message")
        
        assert "Console test message" in caplog.text
    
    def test_logger_different_levels_in_output(self, caplog):
        """Test that different log levels work"""
        logger = setup_logger('test_levels', level='DEBUG', log_to_file=False)
        
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
        
        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text
