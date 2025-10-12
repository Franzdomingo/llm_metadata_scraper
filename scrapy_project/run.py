#!/usr/bin/env python3
"""
Entry point script for running Scrapy spiders

Usage:
    python run.py <spider_name> [options]
    
Examples:
    python run.py kaggle_links --max-pages=10
    python run.py kaggle_metadata --input-file=output/kaggle_output.csv
"""

import sys
import os
from scrapy.cmdline import execute


def main():
    """Main entry point for running spiders"""
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    if len(sys.argv) < 2:
        print("Usage: python run.py <spider_name> [options]")
        print("\nAvailable spiders:")
        print("  kaggle_links     - Scrape Kaggle model links")
        print("  kaggle_metadata  - Scrape Kaggle model metadata")
        print("\nExamples:")
        print("  python run.py kaggle_links")
        print("  python run.py kaggle_links -a max_pages=10")
        print("  python run.py kaggle_metadata")
        print("  python run.py kaggle_metadata -a input_file=output/kaggle_output.csv")
        sys.exit(1)
    
    # Build Scrapy command
    spider_name = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Construct command
    cmd = ['scrapy', 'crawl', spider_name] + args
    
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    
    # Execute Scrapy
    try:
        execute(cmd)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
