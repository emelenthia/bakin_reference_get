"""
Progress tracking utility for the Bakin documentation scraper.

This module provides progress tracking functionality with visual progress bars
and logging capabilities for monitoring scraping operations.
"""

import logging
import time
from typing import Optional, Dict, Any
from tqdm import tqdm
from datetime import datetime


class ProgressTracker:
    """
    Progress tracker with visual progress bars and logging functionality.
    
    Provides comprehensive progress tracking for scraping operations including:
    - Visual progress bars using tqdm
    - Structured logging with different levels
    - Operation timing and statistics
    - Error tracking and reporting
    """
    
    def __init__(self, log_level: int = logging.INFO, log_file: Optional[str] = None):
        """
        Initialize the progress tracker.
        
        Args:
            log_level: Logging level (default: INFO)
            log_file: Optional log file path for file output
        """
        self.current_operation: Optional[str] = None
        self.total_items: int = 0
        self.completed_items: int = 0
        self.start_time: Optional[float] = None
        self.progress_bar: Optional[tqdm] = None
        self.errors: list = []
        self.skipped_items: list = []
        
        # Setup logging
        self.logger = logging.getLogger('bakin_scraper')
        self.logger.setLevel(log_level)
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        self.file_handler = None
        if log_file:
            self.file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.file_handler.setFormatter(file_formatter)
            self.logger.addHandler(self.file_handler)
    
    def start_operation(self, operation_name: str, total_items: int) -> None:
        """
        Start a new operation with progress tracking.
        
        Args:
            operation_name: Name of the operation being tracked
            total_items: Total number of items to process
        """
        self.current_operation = operation_name
        self.total_items = total_items
        self.completed_items = 0
        self.start_time = time.time()
        self.errors.clear()
        self.skipped_items.clear()
        
        # Initialize progress bar
        self.progress_bar = tqdm(
            total=total_items,
            desc=operation_name,
            unit="items",
            ncols=100,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        )
        
        self.logger.info(f"Started operation: {operation_name} (Total items: {total_items})")
    
    def update_progress(self, completed_items: int = None, current_item: str = None) -> None:
        """
        Update the progress of the current operation.
        
        Args:
            completed_items: Number of completed items (if None, increment by 1)
            current_item: Name/description of the current item being processed
        """
        if not self.progress_bar:
            self.logger.warning("No active operation to update progress for")
            return
        
        if completed_items is not None:
            # Set absolute progress
            progress_diff = completed_items - self.completed_items
            self.completed_items = completed_items
            self.progress_bar.update(progress_diff)
        else:
            # Increment by 1
            self.completed_items += 1
            self.progress_bar.update(1)
        
        # Update description with current item
        if current_item:
            self.progress_bar.set_postfix_str(f"Processing: {current_item}")
            self.logger.debug(f"Processing item: {current_item}")
    
    def log_error(self, error: str, context: str = None) -> None:
        """
        Log an error and add it to the error tracking.
        
        Args:
            error: Error message or description
            context: Additional context information (e.g., URL, item name)
        """
        error_entry = {
            'error': error,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        self.errors.append(error_entry)
        
        if context:
            error_msg = f"Error in {context}: {error}"
        else:
            error_msg = f"Error: {error}"
        
        self.logger.error(error_msg)
        
        # Update progress bar with error indication
        if self.progress_bar:
            self.progress_bar.set_postfix_str(f"Error: {error[:30]}...")
    
    def log_skip(self, item: str, reason: str) -> None:
        """
        Log a skipped item and add it to the skip tracking.
        
        Args:
            item: Name/description of the skipped item
            reason: Reason for skipping the item
        """
        skip_entry = {
            'item': item,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        self.skipped_items.append(skip_entry)
        
        self.logger.warning(f"Skipped {item}: {reason}")
        
        # Update progress bar
        if self.progress_bar:
            self.progress_bar.set_postfix_str(f"Skipped: {item}")
    
    def log_info(self, message: str) -> None:
        """
        Log an informational message.
        
        Args:
            message: Information message to log
        """
        self.logger.info(message)
    
    def log_debug(self, message: str) -> None:
        """
        Log a debug message.
        
        Args:
            message: Debug message to log
        """
        self.logger.debug(message)
    
    def complete_operation(self) -> Dict[str, Any]:
        """
        Complete the current operation and return summary statistics.
        
        Returns:
            Dictionary containing operation summary statistics
        """
        if not self.current_operation:
            self.logger.warning("No active operation to complete")
            return {}
        
        # Close progress bar
        if self.progress_bar:
            self.progress_bar.close()
            self.progress_bar = None
        
        # Calculate statistics
        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        success_rate = (self.completed_items / self.total_items * 100) if self.total_items > 0 else 0
        
        summary = {
            'operation': self.current_operation,
            'total_items': self.total_items,
            'completed_items': self.completed_items,
            'errors': len(self.errors),
            'skipped_items': len(self.skipped_items),
            'duration_seconds': duration,
            'success_rate_percent': success_rate,
            'items_per_second': self.completed_items / duration if duration > 0 else 0
        }
        
        # Log completion summary
        self.logger.info(f"Completed operation: {self.current_operation}")
        self.logger.info(f"  Total items: {self.total_items}")
        self.logger.info(f"  Completed: {self.completed_items}")
        self.logger.info(f"  Errors: {len(self.errors)}")
        self.logger.info(f"  Skipped: {len(self.skipped_items)}")
        self.logger.info(f"  Duration: {duration:.2f} seconds")
        self.logger.info(f"  Success rate: {success_rate:.1f}%")
        
        if self.errors:
            self.logger.warning(f"Errors encountered during {self.current_operation}:")
            for error in self.errors[-5:]:  # Show last 5 errors
                context_info = f" ({error['context']})" if error['context'] else ""
                self.logger.warning(f"  - {error['error']}{context_info}")
        
        if self.skipped_items:
            self.logger.info(f"Items skipped during {self.current_operation}: {len(self.skipped_items)}")
        
        # Reset state
        self.current_operation = None
        self.total_items = 0
        self.completed_items = 0
        self.start_time = None
        
        return summary
    
    def get_current_stats(self) -> Dict[str, Any]:
        """
        Get current operation statistics without completing the operation.
        
        Returns:
            Dictionary containing current operation statistics
        """
        if not self.current_operation:
            return {}
        
        current_time = time.time()
        duration = current_time - self.start_time if self.start_time else 0
        
        return {
            'operation': self.current_operation,
            'total_items': self.total_items,
            'completed_items': self.completed_items,
            'errors': len(self.errors),
            'skipped_items': len(self.skipped_items),
            'duration_seconds': duration,
            'progress_percent': (self.completed_items / self.total_items * 100) if self.total_items > 0 else 0,
            'items_per_second': self.completed_items / duration if duration > 0 else 0
        }
    
    def is_active(self) -> bool:
        """
        Check if there's an active operation being tracked.
        
        Returns:
            True if an operation is currently active, False otherwise
        """
        return self.current_operation is not None
    
    def close(self) -> None:
        """
        Close the progress tracker and clean up resources.
        
        This method should be called when the tracker is no longer needed
        to properly close file handlers and clean up resources.
        """
        # Complete any active operation
        if self.is_active():
            self.complete_operation()
        
        # Close file handler if it exists
        if hasattr(self, 'file_handler') and self.file_handler:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)
            self.file_handler = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures proper cleanup."""
        self.close()