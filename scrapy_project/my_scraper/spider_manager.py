"""
Spider Manager Module
Handles spider detection, management, and execution logic
"""

import os
import sys
import importlib
import inspect
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import scrapy
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider


class SpiderManager:
    """Automatically detect and manage Scrapy spiders"""

    def __init__(self, project_dir: Optional[Path] = None):
        """
        Initialize spider manager

        Args:
            project_dir: Project directory (defaults to parent of this file)
        """
        if project_dir:
            self.project_dir = project_dir
        else:
            self.project_dir = Path(__file__).parent.parent

        self.spiders_dir = self.project_dir / 'my_scraper' / 'spiders'
        self.detected_spiders = []
        self._detect_spiders()

    def _detect_spiders(self):
        """Automatically detect all spider classes in the spiders directory"""
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

            except Exception as e:
                print(f"[!] Error loading {module_name}: {e}")

    def _get_spider_description(self, spider_class) -> str:
        """Extract spider description from docstring"""
        if spider_class.__doc__:
            # Get first line of docstring
            lines = spider_class.__doc__.strip().split('\n')
            return lines[0].strip() if lines else "No description"
        return "No description"

    def _get_spider_parameters(self, spider_class) -> List[tuple]:
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

    def get_all_spiders(self) -> List[Dict]:
        """Get list of all detected spiders"""
        return self.detected_spiders

    def get_spider_by_name(self, name: str) -> Optional[Dict]:
        """Get spider info by name"""
        for spider in self.detected_spiders:
            if spider['name'] == name:
                return spider
        return None

    def get_spider_by_index(self, index: int) -> Optional[Dict]:
        """Get spider info by index"""
        if 0 <= index < len(self.detected_spiders):
            return self.detected_spiders[index]
        return None

    def run_spider(self, spider_name: str, spider_args: Optional[Dict] = None) -> bool:
        """
        Run a specific spider

        Args:
            spider_name: Name of the spider to run
            spider_args: Optional arguments to pass to the spider

        Returns:
            True if successful, False otherwise
        """
        spider_info = self.get_spider_by_name(spider_name)

        if not spider_info:
            print(f"[!] Spider '{spider_name}' not found!")
            return False

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
            return True
        except Exception as e:
            print(f"\n[!] Error running spider '{spider_name}': {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_spider_subprocess(self, spider_name: str, spider_args: Optional[Dict] = None) -> bool:
        """
        Run a spider in a subprocess to avoid Twisted reactor issues

        Args:
            spider_name: Name of the spider to run
            spider_args: Optional arguments to pass to the spider

        Returns:
            True if successful, False otherwise
        """
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

            return result.returncode == 0

        except Exception as e:
            print(f"\n[!] Error running spider '{spider_name}': {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_all_spiders(self) -> List[tuple]:
        """
        Run all spiders in sequence, with smart chaining for kaggle spiders

        Returns:
            List of (spider_name, success) tuples
        """
        if not self.detected_spiders:
            print("[!] No spiders detected!")
            return []

        results = []
        kaggle_links_output = None

        for spider in self.detected_spiders:
            # Special handling for kaggle_metadata spider
            if spider['name'] == 'kaggle_metadata':
                # Check if we just ran kaggle_links spider
                if kaggle_links_output:
                    print(f"[+] Using output from kaggle_links spider: {kaggle_links_output}")
                    success = self.run_spider_subprocess(
                        spider['name'],
                        {'input_file': kaggle_links_output}
                    )
                else:
                    # Look for most recent kaggle_links output
                    import glob
                    output_dir = self.project_dir / 'output'
                    json_pattern = str(output_dir / 'kaggle_links_*.json')
                    matching_files = glob.glob(json_pattern)

                    if matching_files:
                        most_recent = max(matching_files, key=os.path.getctime)
                        print(f"[+] Found recent kaggle_links output: {most_recent}")
                        success = self.run_spider_subprocess(
                            spider['name'],
                            {'input_file': most_recent}
                        )
                    else:
                        print("[!] Warning: No kaggle_links output found. Running without input file...")
                        success = self.run_spider_subprocess(spider['name'])
            else:
                # Run normally
                success = self.run_spider_subprocess(spider['name'])

                # If this was kaggle_links spider, find its output file
                if spider['name'] == 'kaggle_links' and success:
                    import glob
                    import time
                    # Wait a moment for file to be written
                    time.sleep(1)
                    output_dir = self.project_dir / 'output'
                    json_pattern = str(output_dir / 'kaggle_links_*.json')
                    matching_files = glob.glob(json_pattern)

                    if matching_files:
                        # Get the most recent file (should be the one we just created)
                        kaggle_links_output = max(matching_files, key=os.path.getctime)
                        print(f"[+] Kaggle links output saved to: {kaggle_links_output}")

            results.append((spider['name'], success))

        return results
