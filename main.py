#!/usr/bin/env python3
"""
Bakin Documentation Scraper
Main entry point for the application
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Scrape Bakin C# documentation and convert to JSON/Markdown"
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.yaml",
        help="Configuration file path (default: config.yaml)"
    )
    
    parser.add_argument(
        "--scrape", 
        action="store_true",
        help="Scrape documentation from Bakin website"
    )
    
    parser.add_argument(
        "--convert", 
        action="store_true",
        help="Convert JSON to Markdown format"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="output",
        help="Output directory (default: output)"
    )
    
    args = parser.parse_args()
    
    if not args.scrape and not args.convert:
        parser.print_help()
        return
    
    print("Bakin Documentation Scraper")
    print(f"Configuration: {args.config}")
    print(f"Output directory: {args.output_dir}")
    
    if args.scrape:
        print("Scraping mode will be implemented in future tasks...")
    
    if args.convert:
        print("Conversion mode will be implemented in future tasks...")


if __name__ == "__main__":
    main()