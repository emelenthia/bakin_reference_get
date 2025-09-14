"""
Tests for the ProgressTracker utility.

Tests progress tracking functionality including visual progress bars,
logging capabilities, and operation statistics.
"""

import unittest
import logging
import time
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.utils.progress_tracker import ProgressTracker


class TestProgressTracker(unittest.TestCase):
    """Test cases for ProgressTracker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = ProgressTracker(log_level=logging.DEBUG)
    
    def tearDown(self):
        """Clean up after tests."""
        if self.tracker.is_active():
            self.tracker.complete_operation()
    
    def test_initialization(self):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker()
        self.assertIsNotNone(tracker.logger)
        self.assertFalse(tracker.is_active())
        self.assertEqual(len(tracker.errors), 0)
        self.assertEqual(len(tracker.skipped_items), 0)
    
    def test_initialization_with_log_file(self):
        """Test ProgressTracker initialization with log file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file = tmp_file.name
        
        try:
            with ProgressTracker(log_file=log_file) as tracker:
                self.assertTrue(os.path.exists(log_file))
                
                # Test that logging to file works
                tracker.log_info("Test message")
            
            # Check if message was written to file after tracker is closed
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("Test message", content)
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    @patch('src.utils.progress_tracker.tqdm')
    def test_start_operation(self, mock_tqdm):
        """Test starting an operation."""
        mock_progress_bar = MagicMock()
        mock_tqdm.return_value = mock_progress_bar
        
        self.tracker.start_operation("Test Operation", 100)
        
        self.assertEqual(self.tracker.current_operation, "Test Operation")
        self.assertEqual(self.tracker.total_items, 100)
        self.assertEqual(self.tracker.completed_items, 0)
        self.assertTrue(self.tracker.is_active())
        self.assertIsNotNone(self.tracker.start_time)
        
        # Verify tqdm was called with correct parameters
        mock_tqdm.assert_called_once_with(
            total=100,
            desc="Test Operation",
            unit="items",
            ncols=100,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        )
    
    @patch('src.utils.progress_tracker.tqdm')
    def test_update_progress_increment(self, mock_tqdm):
        """Test updating progress by incrementing."""
        mock_progress_bar = MagicMock()
        mock_tqdm.return_value = mock_progress_bar
        
        self.tracker.start_operation("Test Operation", 10)
        
        # Test increment by 1 (default)
        self.tracker.update_progress()
        self.assertEqual(self.tracker.completed_items, 1)
        mock_progress_bar.update.assert_called_with(1)
        
        # Test with current item description
        self.tracker.update_progress(current_item="Item 2")
        self.assertEqual(self.tracker.completed_items, 2)
        mock_progress_bar.set_postfix_str.assert_called_with("Processing: Item 2")
    
    @patch('src.utils.progress_tracker.tqdm')
    def test_update_progress_absolute(self, mock_tqdm):
        """Test updating progress with absolute values."""
        mock_progress_bar = MagicMock()
        mock_tqdm.return_value = mock_progress_bar
        
        self.tracker.start_operation("Test Operation", 10)
        
        # Test setting absolute progress
        self.tracker.update_progress(completed_items=5)
        self.assertEqual(self.tracker.completed_items, 5)
        mock_progress_bar.update.assert_called_with(5)
        
        # Test updating from 5 to 8
        self.tracker.update_progress(completed_items=8)
        self.assertEqual(self.tracker.completed_items, 8)
        mock_progress_bar.update.assert_called_with(3)
    
    def test_update_progress_no_active_operation(self):
        """Test updating progress when no operation is active."""
        with patch.object(self.tracker.logger, 'warning') as mock_warning:
            self.tracker.update_progress()
            mock_warning.assert_called_with("No active operation to update progress for")
    
    @patch('src.utils.progress_tracker.tqdm')
    def test_log_error(self, mock_tqdm):
        """Test error logging functionality."""
        mock_progress_bar = MagicMock()
        mock_tqdm.return_value = mock_progress_bar
        
        self.tracker.start_operation("Test Operation", 10)
        
        with patch.object(self.tracker.logger, 'error') as mock_error:
            self.tracker.log_error("Test error", "Test context")
            
            # Check error was logged
            mock_error.assert_called_with("Error in Test context: Test error")
            
            # Check error was added to tracking
            self.assertEqual(len(self.tracker.errors), 1)
            error_entry = self.tracker.errors[0]
            self.assertEqual(error_entry['error'], "Test error")
            self.assertEqual(error_entry['context'], "Test context")
            self.assertIn('timestamp', error_entry)
            
            # Check progress bar was updated
            mock_progress_bar.set_postfix_str.assert_called_with("Error: Test error...")
    
    @patch('src.utils.progress_tracker.tqdm')
    def test_log_skip(self, mock_tqdm):
        """Test skip logging functionality."""
        mock_progress_bar = MagicMock()
        mock_tqdm.return_value = mock_progress_bar
        
        self.tracker.start_operation("Test Operation", 10)
        
        with patch.object(self.tracker.logger, 'warning') as mock_warning:
            self.tracker.log_skip("Test item", "Test reason")
            
            # Check skip was logged
            mock_warning.assert_called_with("Skipped Test item: Test reason")
            
            # Check skip was added to tracking
            self.assertEqual(len(self.tracker.skipped_items), 1)
            skip_entry = self.tracker.skipped_items[0]
            self.assertEqual(skip_entry['item'], "Test item")
            self.assertEqual(skip_entry['reason'], "Test reason")
            self.assertIn('timestamp', skip_entry)
            
            # Check progress bar was updated
            mock_progress_bar.set_postfix_str.assert_called_with("Skipped: Test item")
    
    def test_log_info_and_debug(self):
        """Test info and debug logging."""
        with patch.object(self.tracker.logger, 'info') as mock_info:
            self.tracker.log_info("Test info message")
            mock_info.assert_called_with("Test info message")
        
        with patch.object(self.tracker.logger, 'debug') as mock_debug:
            self.tracker.log_debug("Test debug message")
            mock_debug.assert_called_with("Test debug message")
    
    @patch('src.utils.progress_tracker.tqdm')
    def test_complete_operation(self, mock_tqdm):
        """Test completing an operation."""
        mock_progress_bar = MagicMock()
        mock_tqdm.return_value = mock_progress_bar
        
        self.tracker.start_operation("Test Operation", 10)
        self.tracker.update_progress(completed_items=8)
        self.tracker.log_error("Test error", "context")
        self.tracker.log_skip("Test item", "reason")
        
        # Add a small delay to ensure duration > 0
        time.sleep(0.01)
        
        with patch.object(self.tracker.logger, 'info') as mock_info:
            summary = self.tracker.complete_operation()
            
            # Check summary statistics
            self.assertEqual(summary['operation'], "Test Operation")
            self.assertEqual(summary['total_items'], 10)
            self.assertEqual(summary['completed_items'], 8)
            self.assertEqual(summary['errors'], 1)
            self.assertEqual(summary['skipped_items'], 1)
            self.assertGreater(summary['duration_seconds'], 0)
            self.assertEqual(summary['success_rate_percent'], 80.0)
            self.assertGreater(summary['items_per_second'], 0)
            
            # Check that completion was logged
            self.assertTrue(any("Completed operation: Test Operation" in str(call) for call in mock_info.call_args_list))
            
            # Check progress bar was closed
            mock_progress_bar.close.assert_called_once()
            
            # Check state was reset
            self.assertFalse(self.tracker.is_active())
            self.assertIsNone(self.tracker.current_operation)
    
    def test_complete_operation_no_active(self):
        """Test completing operation when none is active."""
        with patch.object(self.tracker.logger, 'warning') as mock_warning:
            summary = self.tracker.complete_operation()
            mock_warning.assert_called_with("No active operation to complete")
            self.assertEqual(summary, {})
    
    @patch('src.utils.progress_tracker.tqdm')
    def test_get_current_stats(self, mock_tqdm):
        """Test getting current operation statistics."""
        mock_progress_bar = MagicMock()
        mock_tqdm.return_value = mock_progress_bar
        
        # Test with no active operation
        stats = self.tracker.get_current_stats()
        self.assertEqual(stats, {})
        
        # Test with active operation
        self.tracker.start_operation("Test Operation", 20)
        self.tracker.update_progress(completed_items=5)
        
        # Add a small delay to ensure duration > 0
        time.sleep(0.01)
        
        stats = self.tracker.get_current_stats()
        
        self.assertEqual(stats['operation'], "Test Operation")
        self.assertEqual(stats['total_items'], 20)
        self.assertEqual(stats['completed_items'], 5)
        self.assertEqual(stats['errors'], 0)
        self.assertEqual(stats['skipped_items'], 0)
        self.assertGreater(stats['duration_seconds'], 0)
        self.assertEqual(stats['progress_percent'], 25.0)
        self.assertGreater(stats['items_per_second'], 0)
    
    def test_is_active(self):
        """Test checking if tracker is active."""
        self.assertFalse(self.tracker.is_active())
        
        with patch('src.utils.progress_tracker.tqdm'):
            self.tracker.start_operation("Test Operation", 10)
            self.assertTrue(self.tracker.is_active())
            
            self.tracker.complete_operation()
            self.assertFalse(self.tracker.is_active())


if __name__ == '__main__':
    unittest.main()