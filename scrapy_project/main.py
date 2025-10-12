#!/usr/bin/env python3
"""
Main entry point for LLM Metadata Scraper
Automatically detects and runs available Scrapy spiders

Usage:
    python main.py                      # Interactive menu
    python main.py --list               # List all spiders
    python main.py --spider <name>      # Run specific spider
    python main.py --all                # Run all spiders in sequence
"""

import os
import sys
import importlib
import inspect
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import scrapy
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider


class SpiderManager:
    """Automatically detect and manage Scrapy spiders"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.spiders_dir = self.project_dir / 'my_scraper' / 'spiders'
        self.detected_spiders = []
        self._detect_spiders()
    
    def _detect_spiders(self):
        """Automatically detect all spider classes in the spiders directory"""
        print("Detecting available spiders...")
        
        # Add project to path
        sys.path.insert(0, str(self.project_dir))
        
        # Scan spider files
        spider_files = list(self.spiders_dir.glob('*_spider.py'))
        
        for spider_file in spider_files:
            module_name = spider_file.stem
            
            try:
                # Import the module
                module = importlib.import_module(f'my_scraper.spiders.{module_name}')
                
                # Find all Spider subclasses
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, Spider) and 
                        obj is not Spider and 
                        hasattr(obj, 'name') and 
                        obj.name != 'base_spider'):
                        
                        spider_info = {
                            'name': obj.name,
                            'class': obj,
                            'module': module_name,
                            'description': self._get_spider_description(obj),
                            'parameters': self._get_spider_parameters(obj)
                        }
                        self.detected_spiders.append(spider_info)
                        print(f"  [+] Found spider: {obj.name}")
            
            except Exception as e:
                print(f"  [!] Error loading {module_name}: {e}")
        
        print(f"\nTotal spiders detected: {len(self.detected_spiders)}\n")
    
    def _get_spider_description(self, spider_class) -> str:
        """Extract spider description from docstring"""
        if spider_class.__doc__:
            # Get first line of docstring
            lines = spider_class.__doc__.strip().split('\n')
            return lines[0].strip() if lines else "No description"
        return "No description"
    
    def _get_spider_parameters(self, spider_class) -> List[Tuple[str, str, str]]:
        """Extract spider parameters from __init__ method"""
        params = []
        
        try:
            init_method = spider_class.__init__
            sig = inspect.signature(init_method)
            
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'args', 'kwargs']:
                    continue
                
                default = param.default if param.default != inspect.Parameter.empty else None
                param_type = "str"  # Default type
                
                # Try to infer type from default value
                if default is not None:
                    param_type = type(default).__name__
                
                params.append((param_name, param_type, str(default)))
        
        except Exception:
            pass
        
        return params
    
    def list_spiders(self):
        """Display all detected spiders"""
        if not self.detected_spiders:
            print("[!] No spiders detected!")
            return
        
        print("=" * 80)
        print("Available Spiders".center(80))
        print("=" * 80)
        
        for i, spider in enumerate(self.detected_spiders, 1):
            print(f"\n{i}. {spider['name']}")
            print(f"   Description: {spider['description']}")
            
            if spider['parameters']:
                print(f"   Parameters:")
                for param_name, param_type, default in spider['parameters']:
                    default_str = f" (default: {default})" if default != "None" else ""
                    print(f"      - {param_name} ({param_type}){default_str}")
            
            print(f"   Module: {spider['module']}.py")
        
        print("\n" + "=" * 80)
    
    def get_spider_by_name(self, name: str) -> Dict:
        """Get spider info by name"""
        for spider in self.detected_spiders:
            if spider['name'] == name:
                return spider
        return None
    
    def run_spider(self, spider_name: str, spider_args: Dict = None):
        """Run a specific spider"""
        spider_info = self.get_spider_by_name(spider_name)
        
        if not spider_info:
            print(f"[!] Spider '{spider_name}' not found!")
            self.list_spiders()
            return False
        
        print(f"\n{'=' * 80}")
        print(f"Running Spider: {spider_name}".center(80))
        print(f"{'=' * 80}\n")
        
        # Get settings
        os.chdir(self.project_dir)
        settings = get_project_settings()
        
        # Create a fresh crawler process for each spider
        # This is necessary because CrawlerProcess.start() can only be called once
        process = CrawlerProcess(settings)
        
        # Add spider with arguments
        spider_args = spider_args or {}
        process.crawl(spider_info['class'], **spider_args)
        
        # Start crawling
        try:
            process.start()  # This blocks until crawling is finished
            print(f"\n[+] Spider '{spider_name}' completed successfully!")
            return True
        except Exception as e:
            print(f"\n[!] Error running spider '{spider_name}': {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_spiders(self):
        """Run all spiders in sequence"""
        if not self.detected_spiders:
            print("[!] No spiders detected!")
            return
        
        print(f"\nRunning all {len(self.detected_spiders)} spiders in sequence...\n")
        
        results = []
        for spider in self.detected_spiders:
            print(f"\n{'=' * 80}")
            print(f"Starting: {spider['name']}".center(80))
            print(f"{'=' * 80}\n")
            
            # Run each spider in a subprocess to avoid Twisted reactor issues
            success = self._run_spider_subprocess(spider['name'])
            results.append((spider['name'], success))
        
        # Summary
        print(f"\n{'=' * 80}")
        print("Summary".center(80))
        print(f"{'=' * 80}\n")
        
        for spider_name, success in results:
            status = "[+] Success" if success else "[!] Failed"
            print(f"  {spider_name}: {status}")
        
        print(f"\n{'=' * 80}\n")
    
    def _run_spider_subprocess(self, spider_name: str, spider_args: Dict = None):
        """Run a spider in a subprocess to avoid Twisted reactor issues"""
        import subprocess
        
        # Build command to run spider via run.py
        cmd = [sys.executable, 'run.py', spider_name]
        
        # Add arguments if provided
        if spider_args:
            args_str = ','.join([f'{k}={v}' for k, v in spider_args.items()])
            cmd.extend(['-a', args_str])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=False,  # Show output in real-time
                check=False
            )
            
            if result.returncode == 0:
                print(f"\n[+] Spider '{spider_name}' completed successfully!")
                return True
            else:
                print(f"\n[!] Spider '{spider_name}' failed with exit code {result.returncode}")
                return False
                
        except Exception as e:
            print(f"\n[!] Error running spider '{spider_name}': {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def interactive_menu(self):
        """Display interactive menu for spider selection"""
        while True:
            print("\n" + "=" * 80)
            print("LLM Metadata Scraper - Interactive Menu".center(80))
            print("=" * 80)
            
            if not self.detected_spiders:
                print("\n[!] No spiders detected!")
                break
            
            print("\nAvailable Spiders:")
            for i, spider in enumerate(self.detected_spiders, 1):
                print(f"  {i}. {spider['name']} - {spider['description']}")
            
            print(f"\n  {len(self.detected_spiders) + 1}. Run ALL spiders")
            print(f"  0. Exit")
            
            try:
                choice = input("\nSelect spider number (0 to exit): ").strip()
                
                if choice == '0':
                    print("\nGoodbye!")
                    break
                
                choice_num = int(choice)
                
                if choice_num == len(self.detected_spiders) + 1:
                    # Run all spiders
                    self.run_all_spiders()
                    break  # Exit after running all
                
                elif 1 <= choice_num <= len(self.detected_spiders):
                    spider = self.detected_spiders[choice_num - 1]
                    
                    # Ask for parameters
                    spider_args = {}
                    if spider['parameters']:
                        print(f"\nSpider parameters (press Enter to use defaults):")
                        for param_name, param_type, default in spider['parameters']:
                            default_str = f" [{default}]" if default != "None" else ""
                            value = input(f"  {param_name}{default_str}: ").strip()
                            
                            if value:
                                # Convert to appropriate type
                                if param_type == 'int':
                                    spider_args[param_name] = int(value)
                                elif param_type == 'float':
                                    spider_args[param_name] = float(value)
                                elif param_type == 'bool':
                                    spider_args[param_name] = value.lower() in ['true', 'yes', '1', 'y']
                                else:
                                    spider_args[param_name] = value
                    
                    # Run spider
                    self.run_spider(spider['name'], spider_args)
                    break  # Exit after running
                
                else:
                    print(f"[!] Invalid choice! Please select 0-{len(self.detected_spiders) + 1}")
            
            except ValueError:
                print("[!] Invalid input! Please enter a number.")
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                print(f"[!] Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='LLM Metadata Scraper - Automatically detect and run spiders',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Interactive menu
  python main.py --list                             # List all spiders
  python main.py --spider kaggle_links              # Run specific spider
  python main.py --spider kaggle_links --args max_pages=10
  python main.py --spider kaggle_metadata --args input_file=output/file.csv
  python main.py --all                              # Run all spiders
        """
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available spiders'
    )
    
    parser.add_argument(
        '--spider', '-s',
        type=str,
        help='Run specific spider by name'
    )
    
    parser.add_argument(
        '--args', '-a',
        type=str,
        help='Spider arguments in format: key1=value1,key2=value2'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all spiders in sequence'
    )
    
    args = parser.parse_args()
    
    # Initialize spider manager
    manager = SpiderManager()
    
    # Handle different modes
    if args.list:
        manager.list_spiders()
    
    elif args.spider:
        # Parse spider arguments
        spider_args = {}
        if args.args:
            for arg in args.args.split(','):
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    spider_args[key.strip()] = value.strip()
        
        manager.run_spider(args.spider, spider_args)
    
    elif args.all:
        manager.run_all_spiders()
    
    else:
        # Interactive menu
        manager.interactive_menu()


if __name__ == '__main__':
    main()
