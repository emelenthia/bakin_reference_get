"""
Example usage of the ProgressTracker utility.

This example demonstrates how to use the ProgressTracker for monitoring
long-running operations with visual progress bars and logging.
"""

import sys
import os
import time
import random
import logging

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.progress_tracker import ProgressTracker


def simulate_scraping_operation():
    """
    Simulate a web scraping operation with progress tracking.
    
    This example shows how to use ProgressTracker to monitor a batch
    processing operation with errors and skipped items.
    """
    print("=== ProgressTracker Example: Simulated Web Scraping ===\n")
    
    # Initialize progress tracker with INFO level logging
    tracker = ProgressTracker(log_level=logging.INFO, log_file="scraping.log")
    
    # Simulate processing a list of URLs
    urls = [
        "https://example.com/page1",
        "https://example.com/page2", 
        "https://example.com/page3",
        "https://example.com/page4",
        "https://example.com/page5",
        "https://example.com/page6",
        "https://example.com/page7",
        "https://example.com/page8",
        "https://example.com/page9",
        "https://example.com/page10"
    ]
    
    # Start the operation
    tracker.start_operation("Web Scraping Simulation", len(urls))
    
    try:
        for i, url in enumerate(urls):
            # Update progress with current item
            tracker.update_progress(current_item=f"URL {i+1}")
            
            # Simulate processing time
            time.sleep(0.5)
            
            # Simulate random errors and skips
            rand = random.random()
            
            if rand < 0.1:  # 10% chance of error
                tracker.log_error(f"Connection timeout", url)
                continue
            elif rand < 0.2:  # 10% chance of skip
                tracker.log_skip(url, "Already processed")
                continue
            else:
                # Successful processing
                tracker.log_debug(f"Successfully processed {url}")
            
            # Get current stats periodically
            if (i + 1) % 3 == 0:
                stats = tracker.get_current_stats()
                tracker.log_info(f"Progress: {stats['progress_percent']:.1f}% complete")
        
        # Complete the operation and get summary
        summary = tracker.complete_operation()
        
        print(f"\n=== Operation Summary ===")
        print(f"Operation: {summary['operation']}")
        print(f"Total items: {summary['total_items']}")
        print(f"Completed: {summary['completed_items']}")
        print(f"Errors: {summary['errors']}")
        print(f"Skipped: {summary['skipped_items']}")
        print(f"Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"Success rate: {summary['success_rate_percent']:.1f}%")
        print(f"Processing rate: {summary['items_per_second']:.2f} items/sec")
        
    except KeyboardInterrupt:
        tracker.log_error("Operation interrupted by user", "KeyboardInterrupt")
        tracker.complete_operation()
        print("\nOperation interrupted by user")
    except Exception as e:
        tracker.log_error(f"Unexpected error: {str(e)}", "Exception")
        tracker.complete_operation()
        print(f"\nOperation failed: {e}")


def demonstrate_multiple_operations():
    """
    Demonstrate tracking multiple sequential operations.
    """
    print("\n=== Multiple Operations Example ===\n")
    
    tracker = ProgressTracker(log_level=logging.INFO)
    
    # Operation 1: Data collection
    tracker.start_operation("Data Collection", 5)
    for i in range(5):
        tracker.update_progress(current_item=f"Dataset {i+1}")
        time.sleep(0.3)
    summary1 = tracker.complete_operation()
    
    print(f"Data Collection completed in {summary1['duration_seconds']:.2f}s")
    
    # Operation 2: Data processing
    tracker.start_operation("Data Processing", 8)
    for i in range(8):
        tracker.update_progress(current_item=f"Processing batch {i+1}")
        time.sleep(0.2)
        
        # Simulate occasional errors
        if i == 3:
            tracker.log_error("Invalid data format", f"Batch {i+1}")
        elif i == 6:
            tracker.log_skip(f"Batch {i+1}", "Empty dataset")
    
    summary2 = tracker.complete_operation()
    print(f"Data Processing completed in {summary2['duration_seconds']:.2f}s")
    
    # Operation 3: Report generation
    tracker.start_operation("Report Generation", 3)
    for i in range(3):
        tracker.update_progress(current_item=f"Report section {i+1}")
        time.sleep(0.4)
    summary3 = tracker.complete_operation()
    
    print(f"Report Generation completed in {summary3['duration_seconds']:.2f}s")
    
    # Overall summary
    total_time = summary1['duration_seconds'] + summary2['duration_seconds'] + summary3['duration_seconds']
    total_items = summary1['total_items'] + summary2['total_items'] + summary3['total_items']
    total_errors = summary1['errors'] + summary2['errors'] + summary3['errors']
    
    print(f"\n=== Overall Summary ===")
    print(f"Total operations: 3")
    print(f"Total items processed: {total_items}")
    print(f"Total errors: {total_errors}")
    print(f"Total time: {total_time:.2f} seconds")


def demonstrate_logging_levels():
    """
    Demonstrate different logging levels and file output.
    """
    print("\n=== Logging Levels Example ===\n")
    
    # Create tracker with DEBUG level and file output using context manager
    with ProgressTracker(log_level=logging.DEBUG, log_file="debug_example.log") as tracker:
        tracker.start_operation("Logging Demo", 3)
        
        # Demonstrate different log levels
        tracker.log_debug("This is a debug message - detailed information")
        tracker.update_progress(current_item="Item 1")
        
        tracker.log_info("This is an info message - general information")
        tracker.update_progress(current_item="Item 2")
        
        tracker.log_error("This is an error message", "Error context")
        tracker.update_progress(current_item="Item 3")
        
        tracker.log_skip("Item 4", "Demonstration skip")
        
        summary = tracker.complete_operation()
    
    print("Check 'debug_example.log' file for detailed logging output")


if __name__ == "__main__":
    # Run examples
    simulate_scraping_operation()
    demonstrate_multiple_operations()
    demonstrate_logging_levels()
    
    print("\n=== Examples completed ===")
    print("Log files created:")
    print("- scraping.log (from first example)")
    print("- debug_example.log (from logging levels example)")